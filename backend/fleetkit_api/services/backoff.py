from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta


def compute_backoff_seconds(attempt: int, *, base: float = 2.0, cap: float = 300.0) -> float:
    """Exponential backoff with full jitter."""
    exp = min(cap, base * (2 ** max(0, attempt - 1)))
    return random.uniform(0, exp)


def next_retry_at(attempt: int, *, base: float = 2.0, cap: float = 300.0) -> datetime:
    delay = compute_backoff_seconds(attempt, base=base, cap=cap)
    return datetime.now(UTC) + timedelta(seconds=delay)


def describe_policy(attempt: int, max_attempts: int) -> dict:
    return {
        "attempt": attempt,
        "max_attempts": max_attempts,
        "next_delay_seconds": round(compute_backoff_seconds(attempt), 3),
        "exhausted": attempt >= max_attempts,
    }
