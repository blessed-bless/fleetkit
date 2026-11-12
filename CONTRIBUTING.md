# Contributing

1. Fork → branch → PR against `main`.
2. Keep secrets out of the tree (`.env`, raw API keys, bot tokens).
3. Backend: `ruff check` + `pytest` in `backend/`.
4. Frontend: `npm run build` in `frontend/`.
5. Prefer small PRs with a clear why in the description.

## Local checklist

```bash
docker compose up -d postgres redis
cd backend && pip install -e ".[dev]" && pytest -q && ruff check .
cd ../frontend && npm ci && npm run build
```
