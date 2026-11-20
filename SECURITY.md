# Security

- Report vulnerabilities privately to the repository owner on GitHub (Security advisories).
- Never open a public issue with live tokens, passwords, or customer data.
- Rotate `FLEETKIT_SECRET_KEY`, bootstrap password, and API keys after any leak.
- Webhook ingest requires `X-FleetKit-Signature` equal to the endpoint secret. Secrets are stored hashed (SHA-256); the raw value is returned once on create.
- Alert webhook URLs and HTTP health-check targets are checked with the SSRF guard before the API fetches them.
- Job handlers ignore `allow_private` from payloads — private/link-local targets stay blocked.
- Live WebSocket auth uses `Sec-WebSocket-Protocol: fleetkit-jwt, <jwt>` (no JWT in the query string).
- Notification channel configs (`bot_token`, etc.) are redacted in API responses and project export.
- Production (`FLEETKIT_ENV=production`) refuses default secrets, the demo bootstrap password, and SQLite. Use `.env.production.example` as a checklist.
- Prefer the published GHCR images pinned by semver tag, not `:latest`, on real hosts.
