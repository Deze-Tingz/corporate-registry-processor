import time
from collections import defaultdict

from fastapi import HTTPException, Request, status


class RateLimiter:
    """Simple in-memory rate limiter. For production, use Redis-backed."""

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self._hits: dict[str, list[float]] = defaultdict(list)

    def _client_key(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "unknown")
        return ip

    def check(self, request: Request):
        key = self._client_key(request)
        now = time.monotonic()
        # Prune old entries
        self._hits[key] = [t for t in self._hits[key] if now - t < self.window]

        if len(self._hits[key]) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Try again later.",
            )
        self._hits[key].append(now)


# Global instances
general_limiter = RateLimiter(max_requests=120, window_seconds=60)
auth_limiter = RateLimiter(max_requests=10, window_seconds=60)
