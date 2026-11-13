# Security notes

- Bootstrap password is for first boot only — change it.
- API keys are stored as SHA-256 hashes; raw secret shown once.
- Webhook secrets are stored hashed the same way; raw value only on create.
- Secret vault uses HMAC + keystream derived from `FLEETKIT_SECRET_KEY`.
- Webhook ingest requires `X-FleetKit-Signature`.
- SSRF guard runs on alert webhooks, HTTP health checks, and worker HTTP/net jobs.
- `allow_private` in job payloads is ignored.
- WebSocket live feed authenticates via `Sec-WebSocket-Protocol`, not `?token=`.
- Channel configs are redacted in list/export responses.
- Secret reveal writes an audit row.
- Agent routes have an in-memory rate limit (120/min/key).
- Do not commit `.env`, raw keys, bot tokens.
- Prefer project-scoped keys over one global key for all workers.
- Public web nginx no longer proxies `/docs` / `/openapi.json`.
