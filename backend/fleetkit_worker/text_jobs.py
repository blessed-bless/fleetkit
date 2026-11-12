from __future__ import annotations

from collections import Counter
from typing import Any

from fleetkit_worker.handlers import job
from fleetkit_worker.parsers import extract_emails, extract_urls, flatten, require_str


@job("text.stats")
async def text_stats(payload: dict[str, Any]) -> dict[str, Any]:
    text = require_str(payload, "text")
    words = [w for w in text.replace("\n", " ").split(" ") if w]
    return {
        "chars": len(text),
        "words": len(words),
        "lines": text.count("\n") + 1,
        "unique_words": len(set(w.lower() for w in words)),
        "top": Counter(w.lower() for w in words).most_common(10),
    }


@job("text.extract_emails")
async def text_extract_emails(payload: dict[str, Any]) -> dict[str, Any]:
    text = require_str(payload, "text")
    return {"emails": extract_emails(text)}


@job("text.extract_urls")
async def text_extract_urls(payload: dict[str, Any]) -> dict[str, Any]:
    text = require_str(payload, "text")
    return {"urls": extract_urls(text)}


@job("text.flatten_json")
async def text_flatten_json(payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data")
    if not isinstance(data, dict):
        raise ValueError("payload.data must be object")
    return {"flat": flatten(data)}


@job("text.replace")
async def text_replace(payload: dict[str, Any]) -> dict[str, Any]:
    text = require_str(payload, "text")
    old = require_str(payload, "old")
    new = str(payload.get("new", ""))
    count = int(payload.get("count", 0))
    if count > 0:
        return {"text": text.replace(old, new, count)}
    return {"text": text.replace(old, new)}


for _i in range(1, 21):
    def _factory(n: int = _i):
        @job(f"text.demo.{n:02d}")
        async def _handler(payload: dict[str, Any], idx: int = n) -> dict[str, Any]:
            text = str(payload.get("text", ""))
            return {"idx": idx, "len": len(text), "upper": text.upper()[:200]}

        return _handler

    _factory()
