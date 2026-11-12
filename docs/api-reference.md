# API reference (human)

Base: `/api/v1`

## Auth

- `POST /auth/login` `{email,password}` → `{access_token}`
- `GET /auth/me` bearer

## Projects / apps

- `GET|POST /projects`
- `GET /projects/{id}`
- `GET|POST /projects/{id}/api-keys`
- `GET|POST /projects/{id}/apps`
- `GET|PATCH /projects/{id}/apps/{app_id}`

## Jobs / workers / schedules / webhooks

- `GET /projects/{id}/jobs`
- `POST /projects/{id}/apps/{app}/jobs`
- `POST /projects/{id}/jobs/batch`
- `GET /projects/{id}/workers`
- `GET|POST /projects/{id}/apps/{app}/schedules`
- `GET|POST /projects/{id}/apps/{app}/webhooks`
- `POST /hooks/{path_token}` + `X-FleetKit-Signature`

## Agent API (API key)

- `POST /agent/apps/{app}/workers/register`
- `POST /agent/workers/{id}/heartbeat`
- `POST /agent/workers/{id}/claim`
- `POST /agent/apps/{app}/jobs`
- `POST /agent/jobs/{id}/complete|fail`
- `POST /agent/jobs/{id}/logs` and `/logs/batch`
- `POST /agent/metrics`

## Alerts / secrets / DLQ / metrics / ops

- channels, alert-rules, alert-fires, alerts/evaluate
- secrets (+ reveal)
- dead-letters (+ requeue)
- metrics (+ snapshot)
- templates (+ run)
- audit, retention, flags, health-checks, members, invites
- app env vars
- search
- export / import
- websocket `/ws/projects/{id}?token=`

## Overview

- `GET /overview`
- `GET /healthz`
