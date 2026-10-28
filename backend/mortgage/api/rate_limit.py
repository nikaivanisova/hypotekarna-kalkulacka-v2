"""Rate limit for calculations (api/openapi.yaml `TooManyRequests`; Phase 8 decision: a simple limit in the app).

Per client IP, at most `limit` POST /api/v1/calculations requests in any `window` seconds (a sliding
window). Over the limit: 429 problem+json with Retry-After, before the body is read. In memory, so it
holds for one server process; a hosting proxy can replace it when V2 is deployed (D10).

The client IP is the TCP peer address. X-Forwarded-For is not trusted: without a proxy in front
(V2 runs locally, D10), a client could set it to anything.

Setting (environment): MORTGAGE_RATE_LIMIT = "<limit>/<seconds>" (default "30/60"), or "off".
"""
import math
import os
from collections import deque
from dataclasses import dataclass
from typing import Callable

from starlette.types import ASGIApp, Receive, Scope, Send

from mortgage.api.problems import problem

LIMITED_PATH = '/api/v1/calculations'
DEFAULT = '30/60'


@dataclass(frozen=True)
class RateLimit:
    limit: int  # requests
    window: float  # seconds


def rate_limit_from_env() -> RateLimit | None:
    value = os.environ.get('MORTGAGE_RATE_LIMIT', DEFAULT).strip()
    if value.lower() == 'off':
        return None
    parts = [p.strip() for p in value.split('/')]
    if len(parts) != 2 or not all(p.isdigit() for p in parts) or int(parts[0]) < 1 or int(parts[1]) < 1:
        raise ValueError('MORTGAGE_RATE_LIMIT must be "<limit>/<seconds>" with both at least 1, or "off".')
    return RateLimit(int(parts[0]), int(parts[1]))


class RateLimitMiddleware:
    def __init__(self, app: ASGIApp, rate_limit: RateLimit, clock: Callable[[], float],
                 max_clients: int = 10_000) -> None:
        self.app = app
        self.rate_limit = rate_limit
        self.clock = clock
        self.max_clients = max_clients
        self._requests: dict[str, deque[float]] = {}  # client IP → times of its accepted requests

    def tracked_clients(self) -> int:
        return len(self._requests)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope['type'] != 'http' or scope['method'] != 'POST' or scope['path'] != LIMITED_PATH:
            await self.app(scope, receive, send)
            return

        now = self.clock()
        window = self.rate_limit.window
        client = scope.get('client')
        key = client[0] if client else 'unknown'
        times = self._requests.setdefault(key, deque())
        while times and times[0] <= now - window:
            times.popleft()

        if len(times) >= self.rate_limit.limit:
            # Refused requests are not recorded, so retrying does not extend the wait.
            retry_after = max(1, math.ceil(times[0] + window - now))
            await problem(429, headers={'Retry-After': str(retry_after)})(scope, receive, send)
            return

        times.append(now)
        if len(self._requests) > self.max_clients:
            self._drop_idle(now)
        await self.app(scope, receive, send)

    def _drop_idle(self, now: float) -> None:
        """Bounds memory: forget clients with no request inside the window."""
        cutoff = now - self.rate_limit.window
        for key in [k for k, times in self._requests.items() if not times or times[-1] <= cutoff]:
            del self._requests[key]
