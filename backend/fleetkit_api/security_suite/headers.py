from __future__ import annotations

import re

_CRLF = re.compile(r"[\r\n\x00]")


def strip_crlf(value: str) -> str:
    return _CRLF.sub("", value)


def sanitize_header_value(value: str, *, max_len: int = 1024) -> str:
    # Reject CR/LF/NUL instead of stripping — silent cleanup hides injection attempts.
    if _CRLF.search(value):
        raise ValueError("header value contains CR/LF/NUL")
    cleaned = value.strip()
    if len(cleaned) > max_len:
        raise ValueError("header value too long")
    return cleaned


def sanitize_header_map(headers: dict[str, str] | None) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in (headers or {}).items():
        k = sanitize_header_value(str(key), max_len=128)
        if not k or k.lower() in {"host", "content-length", "connection", "transfer-encoding"}:
            continue
        out[k] = sanitize_header_value(str(value))
    return out
