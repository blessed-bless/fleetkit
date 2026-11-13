from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from jose import JWTError

from fleetkit_api.db import SessionLocal
from fleetkit_api.models import User
from fleetkit_api.security import decode_access_token
from fleetkit_api.services.live import live_hub
from fleetkit_api.services.membership import resolve_project_access

router = APIRouter(tags=["live"])


async def _user_from_token(token: str) -> User | None:
    try:
        payload = decode_access_token(token)
    except (JWTError, ValueError):
        return None
    async with SessionLocal() as db:
        return await db.get(User, payload.get("sub"))


@router.websocket("/ws/projects/{project_id}")
async def project_live(websocket: WebSocket, project_id: str) -> None:
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4401)
        return
    user = await _user_from_token(token)
    if user is None:
        await websocket.close(code=4401)
        return
    async with SessionLocal() as db:
        try:
            await resolve_project_access(db, project_id=project_id, user=user)
        except HTTPException:
            await websocket.close(code=4403)
            return

    await websocket.accept()
    queue = await live_hub.subscribe(project_id)
    try:
        await websocket.send_json({"kind": "hello", "project_id": project_id})
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=25)
                await websocket.send_json(
                    {
                        "kind": event.kind,
                        "project_id": event.project_id,
                        "payload": event.payload,
                    }
                )
            except TimeoutError:
                await websocket.send_json({"kind": "ping"})
            # drain client messages (ignore)
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=0.01)
            except (TimeoutError, WebSocketDisconnect):
                pass
    except WebSocketDisconnect:
        pass
    finally:
        await live_hub.unsubscribe(project_id, queue)
