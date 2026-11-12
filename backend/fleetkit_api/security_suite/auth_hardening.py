"""Auth hardening helpers: lockouts, token binding hints, bootstrap warnings."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass


@dataclass
class LockoutState:
    failures: deque[float]
    locked_until: float = 0.0


class LoginProtector:
    def __init__(self, *, max_failures: int = 8, window_seconds: float = 300, lock_seconds: float = 600) -> None:
        self.max_failures = max_failures
        self.window_seconds = window_seconds
        self.lock_seconds = lock_seconds
        self._state: dict[str, LockoutState] = defaultdict(lambda: LockoutState(deque()))

    def _prune(self, state: LockoutState, now: float) -> None:
        while state.failures and now - state.failures[0] > self.window_seconds:
            state.failures.popleft()

    def is_locked(self, key: str) -> bool:
        now = time.monotonic()
        state = self._state[key]
        return state.locked_until > now

    def register_failure(self, key: str) -> None:
        now = time.monotonic()
        state = self._state[key]
        self._prune(state, now)
        state.failures.append(now)
        if len(state.failures) >= self.max_failures:
            state.locked_until = now + self.lock_seconds

    def register_success(self, key: str) -> None:
        self._state.pop(key, None)


login_protector = LoginProtector()


def is_insecure_bootstrap_password(password: str) -> bool:
    return password in {"fleetkit-admin", "admin", "password", "changeme"}
