"""Fast prefilter before deep detector registry scan.

Deep scan over hundreds of detectors is accurate but expensive on every enqueue.
This module runs a tiny compiled regex pass first; only suspicious inputs go deep.
"""

from __future__ import annotations

import re
from functools import lru_cache

_FAST_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("ssrf_local", re.compile(r"(?i)https?://(127\.0\.0\.1|localhost|0\.0\.0\.0|\[::1\])")),
    ("ssrf_meta", re.compile(r"(?i)169\.254\.169\.254|metadata\.google\.internal")),
    ("sqli", re.compile(r"(?i)(\bunion\b.+\bselect\b|' or |; drop |sleep\s*\()")),
    ("xss", re.compile(r"(?i)(<script|javascript:|onerror\s*=)")),
    ("path", re.compile(r"(?i)(\.\./|\.\.\\|/etc/passwd)")),
    ("cmdi", re.compile(r"(?i)(\|\s*bash|\$\(|;\s*rm\s+-rf)")),
    ("log4j", re.compile(r"(?i)\$\{jndi:")),
    ("proto", re.compile(r"(?i)__proto__|constructor\.prototype")),
    ("secretish", re.compile(r"(?i)(api[_-]?key|bearer\s+[a-z0-9\-\._=]{20,}|fk_[A-Za-z0-9_\-]{16,})")),
]


@lru_cache(maxsize=1)
def fast_patterns() -> list[tuple[str, re.Pattern[str]]]:
    return list(_FAST_PATTERNS)


def fast_hits(text: str) -> list[str]:
    return [name for name, pattern in fast_patterns() if pattern.search(text)]


def needs_deep_scan(text: str) -> bool:
    if len(text) > 4000:
        return True
    return bool(fast_hits(text))
