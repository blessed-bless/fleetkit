# Architecture deep dive

## Why DB-backed queues

Redis queues are fine. FleetKit still keeps jobs in Postgres/SQLite so a crashed broker does not erase the truth. Claim uses `FOR UPDATE SKIP LOCKED` on Postgres and a plain ordered select on SQLite smoke mode.

## Processes

1. **API** — FastAPI app, JWT UI auth, API-key agent auth, in-process loops:
   - schedule tick (15s)
   - stale workers
   - health checks
   - alert evaluation (every ~60s)
   - retention (rarer)
2. **Worker** — optional built-in poller OR any SDK process
3. **Web** — React SPA

## Auth boundaries

| Actor | Credential | Can |
|-------|------------|-----|
| Human | JWT | mutate project resources, reveal secrets (audited) |
| Agent | `X-FleetKit-Key` | register/claim/complete/logs/metrics |
| World | webhook signature | enqueue via ingest path only |

## Failure path

```
fail → retry with jitter backoff (scheduled_for)
     → exhausted → DeadLetter + alert-friendly event
```

## Extension points

- Register `@job("name")` handlers in worker process
- Feature flags for gradual rollout
- Export/import project config JSON
- Notification channels for alert fan-out

## Local vs Docker

- Local default DB: SQLite file `fleetkit.dev.db`
- Docker Compose: Postgres + Redis + api + worker + web
- Redis ping is exposed on `/healthz` but jobs do not require Redis yet
