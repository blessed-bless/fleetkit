# API notes

Base path: `/api/v1`

## Agent flow

1. Create project API key in the UI.
2. Create an app, copy its `id`.
3. Register worker:

```http
POST /api/v1/agent/apps/{app_id}/workers/register
X-FleetKit-Key: fk_...
```

4. Loop claim → execute → complete/fail.

## Webhook ingest

```http
POST /api/v1/hooks/{path_token}
X-FleetKit-Signature: {endpoint.secret}
Content-Type: application/json

{"event":"order.paid"}
```

Creates a job named `target_job_name` (default `webhook.received`) on queue `webhooks`.

## Errors

JSON `{"detail":"..."}`. Russian messages for UI-facing auth/project errors; English-ish kinds in event stream (`job.queued`, `worker.registered`).
