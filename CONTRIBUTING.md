# Contributing

1. Fork → branch → PR against `master`.
2. Keep secrets out of the tree (`.env`, raw API keys, bot tokens).
3. Backend: `ruff check` + `pytest` in `backend/`.
4. Frontend: `npm run lint` + `npm run build` in `frontend/`.
5. Prefer small PRs with a clear why in the description.
6. Version bumps go through `python scripts/bump_version.py X.Y.Z` and a `CHANGELOG.md` section. See [docs/release.md](docs/release.md).

## Local checklist

```bash
docker compose up -d postgres redis
cd backend && pip install -e ".[dev]" && pytest -q && ruff check .
cd ../frontend && npm ci && npm run lint && npm run build
cd ../packages/sdk-python && pip install -e ".[dev]" && pytest -q
cd ../cli && pip install -e . && fleetkit --help
```

## Authorship

Commits and tags: `Bogdan Shcherbinin <blessed-bless@users.noreply.github.com>` only.
No AI / Cursor / bot authors, no `Co-authored-by` for agents. See `AGENTS.md`.
