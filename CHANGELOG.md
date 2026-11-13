# Changelog

## 0.1.0

- Control plane: FastAPI API, React dashboard, Postgres/Redis via Docker Compose.
- Queue with claim (`FOR UPDATE SKIP LOCKED`), retry, timeout, DLQ + requeue.
- Workers: register, heartbeat, claim/complete/fail.
- Schedules (cron → job), webhook ingest, alerts, encrypted secrets vault.
- Live WebSocket overview, metrics/logs/search, retention, feature flags, quotas.
- Python SDK (`fleetkit`) and CLI (`fleetkit-cli`).
- Security suite: SSRF guard, secret redaction, payload scanners, login lockout.
- Production path: `docker-compose.prod.yml`, GHCR images, GitHub Releases with SDK/CLI wheels.
- Same-origin UI: nginx proxies `/api`, `/healthz`, `/docs` to the API container.
- Production config refuses default secrets, demo bootstrap password, and SQLite.

## Unreleased

- Multi-user RBAC on every route, Redis streams queue backend, Helm chart (see `docs/roadmap.md`).
