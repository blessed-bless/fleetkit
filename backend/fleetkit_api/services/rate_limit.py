from __future__ import annotations

import time
from collections import defaultdict, deque


class MemoryRateLimiter:
    """Simple sliding-window limiter for API-key / IP throttling."""

    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str, *, limit: int, window_seconds: float) -> bool:
        now = time.monotonic()
        bucket = self._hits[key]
        while bucket and now - bucket[0] > window_seconds:
            bucket.popleft()
        if len(bucket) >= limit:
            return False
        bucket.append(now)
        return True

    def remaining(self, key: str, *, limit: int, window_seconds: float) -> int:
        now = time.monotonic()
        bucket = self._hits[key]
        while bucket and now - bucket[0] > window_seconds:
            bucket.popleft()
        return max(0, limit - len(bucket))


rate_limiter = MemoryRateLimiter()
