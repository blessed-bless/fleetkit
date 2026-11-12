"""Example Telegram bot that reports heartbeats and enqueues jobs into FleetKit.

Requires:
  TELEGRAM_BOT_TOKEN
  FLEETKIT_API_URL / FLEETKIT_API_KEY / FLEETKIT_APP_ID
"""

from __future__ import annotations

import asyncio
import os

import httpx
from fleetkit import FleetKit


async def telegram_loop(token: str, fk: FleetKit, app_id: str) -> None:
    offset = 0
    api = f"https://api.telegram.org/bot{token}"
    async with httpx.AsyncClient(timeout=40) as client:
        while True:
            resp = await client.get(
                f"{api}/getUpdates",
                params={"offset": offset, "timeout": 25},
            )
            resp.raise_for_status()
            for update in resp.json().get("result", []):
                offset = update["update_id"] + 1
                message = update.get("message") or {}
                text = (message.get("text") or "").strip()
                chat_id = (message.get("chat") or {}).get("id")
                if not chat_id:
                    continue
                if text.startswith("/ping"):
                    job = fk.enqueue(app_id=app_id, name="ping", payload={"chat_id": chat_id})
                    await client.post(
                        f"{api}/sendMessage",
                        json={"chat_id": chat_id, "text": f"Закинул job {job['id']}"},
                    )
                elif text.startswith("/start"):
                    await client.post(
                        f"{api}/sendMessage",
                        json={
                            "chat_id": chat_id,
                            "text": "FleetKit bot. Команды: /ping",
                        },
                    )


def main() -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    api_key = os.environ["FLEETKIT_API_KEY"]
    app_id = os.environ["FLEETKIT_APP_ID"]
    base_url = os.getenv("FLEETKIT_API_URL", "http://localhost:8000")
    with FleetKit(base_url=base_url, api_key=api_key) as fk:
        fk.register_worker(app_id=app_id, name="telegram-bot", labels={"kind": "bot"})
        asyncio.run(telegram_loop(token, fk, app_id))


if __name__ == "__main__":
    main()
