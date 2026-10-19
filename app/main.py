import secrets
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal
from uuid import UUID

from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import Settings
from app.data import CITY, DemoAdapter
from app.models import Entity, RecommendRequest
from app.qloo import QlooAdapter
from app.security import AppError, Budget, GlobalBudget, RateLimiter, Sessions, Signer
from app.workflow import run_workflow

STATIC = Path(__file__).parent / "static"


def create_app(settings: Settings | None = None, adapter=None):
    settings = settings or Settings()
    source = adapter or (DemoAdapter() if settings.data_mode == "demo" else QlooAdapter(settings))
    signer = Signer(settings.app_secret.get_secret_value())
    global_budget = GlobalBudget(settings.qloo_global_request_limit)
    sessions = Sessions(global_budget, settings.qloo_scenario_request_limit)
    limiter = RateLimiter(settings.rate_limit_per_minute)

    @asynccontextmanager
    async def lifespan(_app):
        yield
        if hasattr(source, "close"):
            await source.close()

    app = FastAPI(title="TasteDistrict", version="0.1.0", lifespan=lifespan, docs_url=None, redoc_url=None)
    app.state.global_budget = global_budget

    @app.exception_handler(AppError)
    async def handle_error(_request, exc):
        return JSONResponse({"error": {"code": exc.code, "message": exc.message}}, status_code=exc.status)

    @app.exception_handler(RequestValidationError)
    async def handle_validation(_request, _exc):
        # Don't echo input, raw upstream content, or configuration errors.
        return JSONResponse({"error": {"code": "validation", "message": "Check your city, 3–5 distinct interests, and exclusion list."}}, status_code=422)

    @app.middleware("http")
    async def guards(request: Request, call_next):
        is_api = request.url.path.startswith("/api/")
        if is_api and not limiter.allow(request.client.host if request.client else "unknown"):
            return JSONResponse({"error": {"code": "rate_limit", "message": "Too many requests. Please wait a minute."}}, 429, headers={"Retry-After": "60"})
        if request.method == "POST":
            origin = request.headers.get("origin")
            if origin and origin.rstrip("/") != str(request.base_url).rstrip("/"):
                return JSONResponse({"error": {"code": "origin", "message": "Use the application on its own origin."}}, 403)
            size, chunks = 0, []
            async for chunk in request.stream():
                size += len(chunk)
                if size > 24_000:
                    return JSONResponse({"error": {"code": "body_limit", "message": "The request is too large."}}, 413)
                chunks.append(chunk)
            request._body = b"".join(chunks)
        cookie = request.cookies.get("td_session", "")
        try:
            payload = signer.verify(cookie, "session")
            session_id = payload["id"]
        except (AppError, KeyError):
            session_id = secrets.token_urlsafe(24)
            cookie = signer.sign({"kind": "session", "id": session_id})
        request.state.session_id = session_id
        response = await call_next(request)
        if is_api:
            response.set_cookie("td_session", cookie, max_age=3600, httponly=True, samesite="strict", secure=request.url.scheme == "https")
            response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
        return response

    @app.get("/health")
    async def health():
        return {"status": "ok", "mode": source.mode, "upstream_verified": False}

    @app.get("/api/config")
    async def config():
        return {
            "mode": source.mode, "cities": [CITY.model_dump()], "llm_enabled": False,
            "live_configured": source.mode == "live",
            "limits": {"min_interests": 3, "max_interests": 5, "qloo_requests": settings.qloo_scenario_request_limit},
            "warnings": [
                "Demo data: fictional places and synthetic affinities. No live Qloo request is made."
                if source.mode == "demo" else "Live Qloo mode. City and three-zone coverage must be verified with the event key.",
                "Exploration zones are authored comparison areas, not official neighborhood boundaries.",
            ],
        }

    @app.get("/api/search")
    async def search(request: Request, q: str = Query(min_length=1, max_length=100), category: Literal["artist", "movie", "book", "place"] = "artist"):
        if not q.strip():
            raise AppError("empty_query", "Enter an artist, film, book, or place name.")
        session = sessions.get(request.state.session_id)
        async with session.lock:
            entities = await source.search(q.strip(), category, session.budget)
            results = [
                {**entity.model_dump(), "token": signer.sign({"kind": "entity", "mode": source.mode, "session": request.state.session_id, "entity": entity.model_dump()})}
                for entity in entities
            ]
            return {"mode": source.mode, "entities": results, "requests_used": session.budget.used}

    @app.post("/api/recommend")
    async def recommend(body: RecommendRequest, request: Request):
        entities = []
        for token in body.interest_tokens:
            payload = signer.verify(token, "entity")
            if payload.get("mode") != source.mode or payload.get("session") != request.state.session_id:
                raise AppError("invalid_selection", "Search for your interests again in this browser session.")
            entities.append(Entity.model_validate(payload["entity"]))
        if len({item.id for item in entities}) != len(entities):
            raise AppError("duplicate_interest", "Choose 3–5 distinct interests.")
        if source.mode == "live":
            try:
                for value in body.excluded_place_ids:
                    UUID(value)
            except ValueError:
                raise AppError("invalid_exclusion", "The excluded place identifier is invalid.") from None
        session = sessions.get(request.state.session_id)
        async with session.lock:
            result = await run_workflow(entities, body, source, session.budget)
            # A successful recommendation closes the scenario. Subsequent edits
            # start a fresh bounded scenario; the global allowance never resets.
            session.budget = Budget(global_budget, settings.qloo_scenario_request_limit)
            return result

    @app.post("/api/session/reset")
    async def reset(request: Request):
        session = sessions.get(request.state.session_id)
        async with session.lock:
            session.budget = Budget(global_budget, settings.qloo_scenario_request_limit)
        return {"status": "ok"}

    @app.get("/")
    async def index():
        return FileResponse(STATIC / "index.html", headers={"Cache-Control": "no-cache"})

    # Only this fixed static directory is public; .env and project files cannot be served.
    app.mount("/static", StaticFiles(directory=STATIC, check_dir=False), name="static")
    return app


app = create_app()
