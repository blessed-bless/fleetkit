"""Tiny in-process TTL cache for hot read endpoints."""

from __future__ import annotations

import time
from collections.abc import Hashable
from dataclasses import dataclass
from threading import Lock
from typing import Any


@dataclass
class _Entry:
    value: Any
    expires_at: float


class TtlCache:
    def __init__(self) -> None:
        self._data: dict[Hashable, _Entry] = {}
        self._lock = Lock()

    def get(self, key: Hashable) -> Any | None:
        now = time.monotonic()
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return None
            if entry.expires_at < now:
                self._data.pop(key, None)
                return None
            return entry.value

    def set(self, key: Hashable, value: Any, *, ttl_seconds: float) -> None:
        with self._lock:
            self._data[key] = _Entry(value=value, expires_at=time.monotonic() + ttl_seconds)

    def invalidate_prefix(self, prefix: str) -> None:
        with self._lock:
            dead = [k for k in self._data if isinstance(k, tuple) and k and k[0] == prefix]
            for key in dead:
                self._data.pop(key, None)


overview_cache = TtlCache()
