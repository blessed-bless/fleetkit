# FleetKit Backend

FastAPI control plane and Redis-backed worker runtime.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
uvicorn fleetkit_api.main:app --reload
```

Worker process:

```bash
python -m fleetkit_worker
```
