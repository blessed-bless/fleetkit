from __future__ import annotations

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError
from sqlalchemy import select

from fleetkit_api.db import SessionLocal
from fleetkit_api.models import Project, User
from fleetkit_api.security import decode_access_token
from fleetkit_api.services.live import live_hub

router = APIRouter(tags=["live"])

# Browser WebSocket cannot set Authorization; use subprotocol instead of ?token=.
_WS_AUTH_PROTOCOL = "fleetkit-jwt"


def token_from_websocket(websocket: WebSocket) -> str | None:
    """Extract JWT from Sec-WebSocket-Protocol: fleetkit-jwt, <jwt>."""
    header = websocket.headers.get("sec-websocket-protocol")
    if not header:
        return None
    parts = [part.strip() for part in header.split(",") if part.strip()]
    if len(parts) >= 2 and parts[0] == _WS_AUTH_PROTOCOL:
        return parts[1]
    # Also accept fleetkit.<jwt> as a single protocol token.
    for part in parts:
        if part.startswith("fleetkit.") and part != "fleetkit.jwt":
            return part.removeprefix("fleetkit.")
    return None


async def _user_from_token(token: str) -> User | None:
    try:
        payload = decode_access_token(token)
    except (JWTError, ValueError):
        return None
    async with SessionLocal() as db:
        return await db.get(User, payload.get("sub"))


@router.websocket("/ws/projects/{project_id}")
async def project_live(websocket: WebSocket, project_id: str) -> None:
    token = token_from_websocket(websocket)
    if not token:
        await websocket.close(code=4401)
        return
    user = await _user_from_token(token)
    if user is None:
        await websocket.close(code=4401)
        return
    async with SessionLocal() as db:
        project = await db.get(Project, project_id)
        if project is None or project.owner_id != user.id:
            from fleetkit_api.models_ext import ProjectMember

            member = await db.scalar(
                select(ProjectMember).where(
                    ProjectMember.project_id == project_id,
                    ProjectMember.user_id == user.id,
                )
            )
            if member is None and (project is None or project.owner_id != user.id):
                await websocket.close(code=4403)
                return

    await websocket.accept(subprotocol=_WS_AUTH_PROTOCOL)
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
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=0.01)
            except (TimeoutError, WebSocketDisconnect):
                pass
    except WebSocketDisconnect:
        pass
    finally:
        await live_hub.unsubscribe(project_id, queue)
