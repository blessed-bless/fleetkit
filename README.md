# FleetKit

Self-hosted control plane for a fleet of bots, Python workers, cron jobs and inbound webhooks.

Один API + dashboard: регистрируешь воркеры, ставишь jobs в очередь, смотришь heartbeats и фейлы. SDK на Python. Docker Compose из коробки.

## Что внутри

- **API** — FastAPI, JWT для UI, API-ключи для агентов
- **Queue** — jobs с retry, timeout, claim через `FOR UPDATE SKIP LOCKED`
- **Workers** — register + heartbeat + claim/complete/fail
- **Schedules** — cron → job
- **Webhooks** — публичный ingest с секретом → job
- **Dashboard** — React (обзор, apps, jobs, workers, schedules, webhooks, templates, health, ops, audit, ключи)
- **SDK** — `packages/sdk-python` (sync + async)
- **CLI** — `packages/cli` (`fleetkit login|overview|enqueue|dlq|...`)
- **Alerts** — правила вида `queue.depth>20`, каналы Telegram/webhook
- **Secrets vault** — шифрованные секреты проекта
- **DLQ** — dead letter + requeue
- **Logs / metrics / search / health checks / retention / feature flags**
- **Live WebSocket** — `/api/v1/ws/projects/{id}?token=...`
- **Security suite** — SSRF guard, CRLF rejection, secret redaction, payload scanners, login lockout, RBAC helpers
- **Unique plugins/detectors** — hundreds of distinct transform jobs + input detectors (not stub clones)
- **Examples** — HTTP worker, Telegram bot, 25 recipe workers

## Быстрый старт (Docker)

```bash
cp .env.example .env
docker compose up --build
```

- API: http://localhost:8000/docs
- UI: http://localhost:8080
- Логин: `admin@example.com` / `fleetkit-admin` (меняется в `.env`)

## Локальная разработка

Backend по умолчанию поднимается на SQLite (без Docker):

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn fleetkit_api.main:app --reload --port 8000
```

Для Postgres + Redis:

```bash
docker compose up -d postgres redis
set FLEETKIT_DATABASE_URL=postgresql+asyncpg://fleetkit:fleetkit@localhost:5432/fleetkit
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

SDK + example worker:

```bash
cd packages/sdk-python
pip install -e .
# в UI: Apps → создать app, Ключи → выпустить ключ
set FLEETKIT_API_KEY=fk_...
set FLEETKIT_APP_ID=...
python ../../examples/http-worker/worker.py
```

## Архитектура

```
Dashboard (React) ──JWT──▶ FleetKit API ──▶ Postgres
                              │
Agent SDK / workers ─API key─┘
                              │
                         Redis (готов под расширения)
Scheduler loop (in API) ──cron──▶ enqueue jobs
Webhook ingest ──────────────▶ enqueue jobs
```

## HTTP surface (коротко)

| Метод | Путь | Кто |
|------|------|-----|
| POST | `/api/v1/auth/login` | UI |
| GET | `/api/v1/overview` | UI |
| POST | `/api/v1/projects/{id}/apps` | UI |
| POST | `/api/v1/projects/{id}/apps/{app}/jobs` | UI |
| POST | `/api/v1/agent/apps/{app}/workers/register` | worker |
| POST | `/api/v1/agent/workers/{id}/claim` | worker |
| POST | `/api/v1/hooks/{token}` | внешний мир |

Полный OpenAPI: `/docs`.

## Документация

- [docs/architecture.md](docs/architecture.md)
- [docs/api.md](docs/api.md)
- [docs/ru/README.md](docs/ru/README.md)

## Лицензия

MIT © Bogdan Shcherbinin
