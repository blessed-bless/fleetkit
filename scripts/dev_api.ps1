$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot\..\backend"
if (-not (Test-Path .venv)) { python -m venv .venv }
.\.venv\Scripts\python -m pip install -e ".[dev]" | Out-Null
$env:FLEETKIT_DATABASE_URL = "sqlite+aiosqlite:///./fleetkit.dev.db"
$env:FLEETKIT_REDIS_URL = "redis://localhost:6379/0"
$env:FLEETKIT_SECRET_KEY = "local-dev-secret"
.\.venv\Scripts\python -m uvicorn fleetkit_api.main:app --reload --host 127.0.0.1 --port 8000
