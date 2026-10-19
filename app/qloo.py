"""Documented event HTTP surfaces; schema evidence is linked in docs/SOURCES.md.

No upstream responses are logged or saved. Local scores use Qloo candidate order,
not undocumented affinity fields or a probability of personal compatibility.
"""

import asyncio
import json
import math
from uuid import UUID

import httpx

from app.models import Entity, Place
from app.security import AppError

TYPES = {kind: f"urn:entity:{kind}" for kind in ("artist", "movie", "book", "place")}


class QlooAdapter:
    mode = "live"

    def __init__(self, settings, client: httpx.AsyncClient | None = None):
        self.settings = settings
        self.client = client or httpx.AsyncClient(
            base_url=settings.qloo_base_url,
            timeout=httpx.Timeout(settings.qloo_timeout_seconds),
            follow_redirects=False,
            trust_env=False,
        )

    async def close(self):
        await self.client.aclose()

    async def _get(self, path: str, params: dict, budget):
        # Paths are constant at the call sites and redirects are never followed.
        for attempt in range(2):
            budget.consume()
            try:
                async with self.client.stream(
                    "GET", path, params=params,
                    headers={"X-Api-Key": self.settings.qloo_api_key.get_secret_value()},
                ) as response:
                    if response.status_code in (401, 403):
                        raise AppError("qloo_auth", "Qloo rejected the event credential. The operator must check the server-side key.", 503)
                    if response.status_code == 429 or response.status_code >= 500:
                        if attempt == 0:
                            await asyncio.sleep(0.25)
                            continue
                        raise AppError("qloo_busy", "Qloo is busy or its rate limit was reached. Try again shortly.", 503)
                    if response.status_code != 200:
                        raise AppError("qloo_request", "Qloo could not accept this query. Try different interests.", 502)
                    chunks, size = [], 0
                    async for chunk in response.aiter_bytes():
                        size += len(chunk)
                        if size > 2_000_000:
                            raise AppError("qloo_schema", "Qloo returned an unexpectedly large response.", 502)
                        chunks.append(chunk)
                    try:
                        data = json.loads(b"".join(chunks))
                    except (ValueError, UnicodeError):
                        raise AppError("qloo_schema", "Qloo returned an unreadable response. Please try again.", 502) from None
                    if not isinstance(data, dict) or data.get("success") is not True:
                        raise AppError("qloo_schema", "Qloo did not return a successful result.", 502)
                    return data
            except (httpx.TimeoutException, httpx.TransportError):
                if attempt == 0:
                    await asyncio.sleep(0.25)
                    continue
                raise AppError("qloo_timeout", "Qloo did not respond in time. Please try again.", 504) from None

    @staticmethod
    def _id(item):
        try:
            return str(UUID(str(item.get("entity_id", ""))))
        except (ValueError, TypeError, AttributeError):
            return None

    @staticmethod
    def _has_type(item, kind):
        return item.get("subtype") == TYPES[kind]

    async def search(self, query, category, budget):
        data = await self._get("/search", {"query": query, "types": TYPES[category], "take": 8}, budget)
        rows = data.get("results")
        if not isinstance(rows, list):
            raise AppError("qloo_schema", "Qloo search returned an unexpected format.", 502)
        entities, seen = [], set()
        for row in rows[:50]:
            if not isinstance(row, dict):
                continue
            entity_id = self._id(row)
            # Only the current documented taxonomy is accepted; live shape must be verified.
            matching_type = self._has_type(row, category)
            name = row.get("name")
            if not entity_id or entity_id in seen or not matching_type or not isinstance(name, str) or not name.strip() or len(name) > 200:
                continue
            seen.add(entity_id)
            # Only verified, displayable metadata. No guessed biographies/years.
            city = row.get("city")
            subtitle = f"{category.title()} · Qloo entity"
            disambiguation = row.get("disambiguation")
            if isinstance(disambiguation, str) and disambiguation.strip():
                subtitle += f" · {disambiguation.strip()[:180]}"
            if isinstance(city, str) and len(city) < 100:
                subtitle += f" · {city}"
            entities.append(Entity(id=entity_id, name=name.strip(), type=category, subtitle=subtitle))
        if rows and not entities:
            raise AppError("qloo_schema", "Search returned entities this build cannot validate. The operator must check the live schema.", 502)
        return entities[:8]

    async def recommend(self, entities, city, excluded, budget, expand=False):
        params = {
            "filter.type": "urn:entity:place",
            "signal.interests.entities": ",".join(entity.id for entity in entities),
            "filter.location.query": "New York City",
            "filter.location.radius": 0,
            "take": 50 if expand else 30,
        }
        if excluded:
            params["filter.exclude.entities"] = ",".join(excluded)
        data = await self._get("/v2/insights", params, budget)
        results = data.get("results")
        rows = results.get("entities") if isinstance(results, dict) else None
        if not isinstance(rows, list):
            raise AppError("qloo_schema", "Qloo recommendations returned an unexpected format.", 502)
        places = []
        for index, row in enumerate(rows[:50]):
            if not isinstance(row, dict) or row.get("is_closed") is True or not self._has_type(row, "place"):
                continue
            entity_id, name = self._id(row), row.get("name")
            lat, lon = row.get("lat"), row.get("lon")
            # Coordinates here follow the current official Places taxonomy.
            if (not entity_id or not isinstance(name, str) or not name.strip() or len(name) > 200
                or isinstance(lat, bool) or isinstance(lon, bool)
                or not isinstance(lat, (int, float)) or not isinstance(lon, (int, float))
                or not math.isfinite(lat) or not math.isfinite(lon)
                or not -90 <= lat <= 90 or not -180 <= lon <= 180):
                continue
            places.append(Place(
                id=entity_id, name=name.strip(), category="Place",
                latitude=lat, longitude=lon,
                # Fixed denominator keeps scores stable when take expands 30→50.
                score=1 - index / 50,
                evidence=[f"Qloo returned this place for your combined selected interests (candidate {index + 1} of {len(rows)}).", "Coordinates were supplied by Qloo; current opening status has not been verified."],
            ))
        return places
