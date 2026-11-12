from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

Handler = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]

_REGISTRY: dict[str, Handler] = {}


def job(name: str) -> Callable[[Handler], Handler]:
    def decorator(fn: Handler) -> Handler:
        _REGISTRY[name] = fn
        return fn

    return decorator


def get_handler(name: str) -> Handler | None:
    if name in _REGISTRY:
        return _REGISTRY[name]
    if name.startswith("schedule:"):
        return _REGISTRY.get("schedule.*")
    return _REGISTRY.get("*")


@job("ping")
async def handle_ping(payload: dict[str, Any]) -> dict[str, Any]:
    return {"pong": True, "payload": payload}


@job("webhook.received")
async def handle_webhook(payload: dict[str, Any]) -> dict[str, Any]:
    return {"ok": True, "webhook": payload.get("body"), "handled_by": "webhook"}


@job("schedule.*")
async def handle_schedule(payload: dict[str, Any]) -> dict[str, Any]:
    return {"ok": True, "echo": payload, "handled_by": "schedule"}


@job("*")
async def handle_default(payload: dict[str, Any]) -> dict[str, Any]:
    await asyncio.sleep(0.05)
    return {"ok": True, "echo": payload}
