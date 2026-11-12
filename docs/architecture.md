# Architecture

## Domains

1. **Project** — tenant boundary. Owns apps and API keys.
2. **App** — logical unit (bot / worker / cron / webhook target).
3. **Worker** — running process that heartbeats and claims jobs.
4. **Job** — unit of work with payload, attempts, status.
5. **Schedule** — cron expression that enqueues jobs.
6. **WebhookEndpoint** — public token + secret → job.
7. **Event** — append-only audit stream for the dashboard.

## Job lifecycle

```
queued → running → succeeded
                 ↘ failed (after max_attempts)
                 ↘ timed_out (future sweeper)
```

Claim uses `SELECT ... FOR UPDATE SKIP LOCKED` so multiple workers can poll safely.

## Auth

- Dashboard: JWT bearer from `/auth/login`
- Agents: `X-FleetKit-Key` (SHA-256 stored, raw shown once)

## Processes

| Process | Role |
|---------|------|
| `fleetkit_api` | HTTP API + in-process scheduler tick every 15s |
| `fleetkit_worker` | Optional built-in poller (needs API key + app id) |
| `examples/*` | External agents via SDK |

## Storage

Postgres is source of truth. Redis is wired for future fan-out / pubsub; jobs today are DB-backed so a single-node deploy stays simple.
