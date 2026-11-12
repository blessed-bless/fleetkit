# Operator handbook

## Day-1

1. Bring the stack up (`docker compose up --build` or local SQLite API).
2. Login as bootstrap admin.
3. Create an app for each bot/parser.
4. Mint an API key per environment (dev/prod).
5. Point workers at the API with `FLEETKIT_API_KEY` + `FLEETKIT_APP_ID`.

## Day-2 habits

- Watch `Failed 24h` on the overview.
- Keep schedules timezone-aware; default is UTC.
- Prefer small jobs (`ping`, fetch-one-url) over long blocking work inside a single claim.
- Rotate keys when a laptop leaves the fleet.

## Failure modes

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Worker never appears | Wrong key / app id | Re-check Settings + Apps IDs |
| Jobs stuck in queued | No worker online | Start example worker / docker worker |
| Webhook 401 | Bad signature header | Send `X-FleetKit-Signature` = endpoint secret |
| Login 422 on email | Reserved domain | Use a normal domain like `example.com` |
