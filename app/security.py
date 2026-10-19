"""Small in-memory guards. No API responses, queries, or keys are logged or persisted."""

import asyncio
import base64
import hashlib
import hmac
import json
import secrets
import time
from collections import OrderedDict, deque
from dataclasses import dataclass, field


class AppError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        self.code, self.message, self.status = code, message, status
        super().__init__(message)


class GlobalBudget:
    def __init__(self, limit: int):
        self.limit = limit
        self.used = 0

    def consume(self):
        if self.used >= self.limit:
            raise AppError("global_budget", "The demo's upstream request allowance is exhausted. Please contact the operator.", 503)
        self.used += 1


class Budget:
    def __init__(self, global_budget: GlobalBudget, max_requests: int = 10):
        self.used = 0
        self.max_requests = max_requests
        self.global_budget = global_budget

    def consume(self):
        if self.used >= self.max_requests:
            raise AppError("scenario_budget", "This scenario reached its Qloo request limit. Start a new scenario to continue.", 429)
        self.global_budget.consume()
        self.used += 1


class Signer:
    def __init__(self, secret: str = ""):
        self.secret = (secret or secrets.token_urlsafe(48)).encode()

    def sign(self, value: dict, lifetime: int = 3600):
        payload = {**value, "exp": int(time.time()) + lifetime}
        data = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode().rstrip("=")
        sig = hmac.new(self.secret, data.encode(), hashlib.sha256).hexdigest()
        return f"{data}.{sig}"

    def verify(self, token: str, kind: str):
        try:
            if len(token) > 4096:
                raise ValueError
            data, sig = token.split(".")
            expected = hmac.new(self.secret, data.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(sig, expected):
                raise ValueError
            payload = json.loads(base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)))
            if payload["exp"] < time.time() or payload["kind"] != kind:
                raise ValueError
            return payload
        except (ValueError, KeyError, TypeError, UnicodeError):
            raise AppError("invalid_selection", "Your selection expired or is invalid. Search for your interests again.") from None


@dataclass
class Session:
    budget: Budget
    touched: float = field(default_factory=time.monotonic)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class Sessions:
    def __init__(self, global_budget: GlobalBudget, limit: int):
        self.items: OrderedDict[str, Session] = OrderedDict()
        self.global_budget, self.limit = global_budget, limit

    def get(self, session_id: str):
        now = time.monotonic()
        session = self.items.get(session_id)
        if session is None or now - session.touched > 3600:
            session = Session(Budget(self.global_budget, self.limit))
            self.items[session_id] = session
        session.touched = now
        self.items.move_to_end(session_id)
        while len(self.items) > 2000:
            self.items.popitem(last=False)
        return session


class RateLimiter:
    def __init__(self, limit: int):
        self.limit = limit
        self.clients: OrderedDict[str, deque] = OrderedDict()

    def allow(self, address: str):
        now = time.monotonic()
        events = self.clients.setdefault(address, deque())
        self.clients.move_to_end(address)
        while events and events[0] <= now - 60:
            events.popleft()
        while len(self.clients) > 5000:
            self.clients.popitem(last=False)
        if len(events) >= self.limit:
            return False
        events.append(now)
        return True
