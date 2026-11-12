# Security

- Report vulnerabilities privately to the repository owner on GitHub.
- Never open a public issue with live tokens, passwords, or customer data.
- Rotate `FLEETKIT_SECRET_KEY`, bootstrap password, and API keys after any leak.
- Webhook endpoints require `X-FleetKit-Signature` equal to the endpoint secret.
