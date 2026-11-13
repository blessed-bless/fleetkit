# Security

- Report vulnerabilities privately to the repository owner on GitHub (Security advisories).
- Never open a public issue with live tokens, passwords, or customer data.
- Rotate `FLEETKIT_SECRET_KEY`, bootstrap password, and API keys after any leak.
- Webhook endpoints require `X-FleetKit-Signature` equal to the endpoint secret.
- Production (`FLEETKIT_ENV=production`) refuses default secrets, the demo bootstrap password, and SQLite. Use `.env.production.example` as a checklist.
- Prefer the published GHCR images pinned by semver tag, not `:latest`, on real hosts.
