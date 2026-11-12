# Security notes

- Bootstrap password is for first boot only — change it.
- API keys are stored as SHA-256 hashes; raw secret shown once.
- Secret vault uses HMAC + keystream derived from `FLEETKIT_SECRET_KEY`.
- Webhook ingest requires `X-FleetKit-Signature`.
- Secret reveal writes an audit row.
- Agent routes have an in-memory rate limit (120/min/key).
- Do not commit `.env`, raw keys, bot tokens.
- Prefer project-scoped keys over one global key for all workers.
