# Releases & packages

FleetKit ships versioned GitHub Releases and container images on GHCR (GitHub Packages).

## What a release publishes

| Artifact | Where |
|----------|--------|
| GitHub Release notes + SDK/CLI wheels | [Releases](https://github.com/blessed-bless/fleetkit/releases) |
| `ghcr.io/blessed-bless/fleetkit-api` | Packages |
| `ghcr.io/blessed-bless/fleetkit-web` | Packages |

Trigger: push a tag `vX.Y.Z` (workflow `.github/workflows/release.yml`).

## Cut a release

1. Update `CHANGELOG.md` with a `## X.Y.Z` section.
2. Sync versions:

```bash
python scripts/bump_version.py X.Y.Z
```

3. Commit, merge to `master`.
4. Tag and push:

```bash
git tag -a vX.Y.Z -m "FleetKit X.Y.Z"
git push origin vX.Y.Z
```

5. Wait for the `release` workflow. Images appear under Packages; wheels hang on the Release.
6. First push only: open each new GHCR package → Package settings → Change visibility → Public (so `docker pull` works without login).

Rebuild an existing tag via Actions → **release** → **Run workflow** (pass `vX.Y.Z`).

## Install from a release

SDK / CLI (from Release assets or a local build):

```bash
pip install https://github.com/blessed-bless/fleetkit/releases/download/v0.1.0/fleetkit-0.1.0-py3-none-any.whl
pip install https://github.com/blessed-bless/fleetkit/releases/download/v0.1.0/fleetkit_cli-0.1.0-py3-none-any.whl
```

Containers:

```bash
docker pull ghcr.io/blessed-bless/fleetkit-api:0.1.0
docker pull ghcr.io/blessed-bless/fleetkit-web:0.1.0
```

Production compose:

```bash
cp .env.production.example .env
# edit secrets
docker compose -f docker-compose.prod.yml --env-file .env up -d
```

UI listens on `:8080` and proxies `/api` + `/healthz` to the API container.

## Version files

`scripts/bump_version.py` keeps these in sync:

- `backend/pyproject.toml`, `fleetkit_api/__init__.py`, `fleetkit_worker/__init__.py`
- `packages/sdk-python` + `packages/cli`
- `frontend/package.json`
