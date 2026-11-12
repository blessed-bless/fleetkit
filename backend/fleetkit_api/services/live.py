"""In-memory pub/sub hub for dashboard live updates."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from dataclasses import dataclass
from typing import Any


@dataclass
class LiveEvent:
    project_id: str
    kind: str
    payload: dict[str, Any]


class LiveHub:
    def __init__(self) -> None:
        self._subs: dict[str, set[asyncio.Queue[LiveEvent]]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def subscribe(self, project_id: str) -> asyncio.Queue[LiveEvent]:
        queue: asyncio.Queue[LiveEvent] = asyncio.Queue(maxsize=200)
        async with self._lock:
            self._subs[project_id].add(queue)
        return queue

    async def unsubscribe(self, project_id: str, queue: asyncio.Queue[LiveEvent]) -> None:
        async with self._lock:
            self._subs[project_id].discard(queue)

    async def publish(self, project_id: str, kind: str, payload: dict[str, Any]) -> None:
        event = LiveEvent(project_id=project_id, kind=kind, payload=payload)
        async with self._lock:
            targets = list(self._subs.get(project_id, set()))
        for queue in targets:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
                try:
                    queue.put_nowait(event)
                except asyncio.QueueFull:
                    pass


live_hub = LiveHub()
