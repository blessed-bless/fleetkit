# Feature map

## Control plane

- Projects, apps, API keys, JWT dashboard auth
- Multi-user RBAC: owner / admin / operator / viewer on project routes
- Invites (create / accept / decline / revoke) + local register
- Job queue with claim/complete/fail, retry + jitter backoff
- Dead letter queue + requeue
- Cron schedules
- Webhook ingest with shared secret
- Worker register/heartbeat + stale offline marker

## Observability

- Events stream on overview
- Job log chunks (agent append / UI read)
- Metric samples + fleet snapshot
- Health checks (HTTP / worker heartbeat)
- Live WebSocket fan-out

## Safety / ops

- Encrypted secrets vault
- App env vars (secret-capable)
- Alert rules + notification channels
- Retention policies
- Audit log
- Feature flags
- Project export/import
- Search across apps/jobs/workers/events/DLQ

## Extensibility

- Python SDK (sync/async)
- CLI (`fleetkit`)
- Built-in worker job catalog (`http.fetch`, `util.hash`, demo prefixes...)
- Recipe examples under `examples/recipes`
