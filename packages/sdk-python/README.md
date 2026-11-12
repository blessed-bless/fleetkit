# fleetkit (Python SDK)

```bash
pip install -e .
```

```python
from fleetkit import FleetKit

client = FleetKit(base_url="http://localhost:8000", api_key="fk_...")
worker = client.register_worker(app_id="...", name="parser-1")
job = client.claim(worker_id=worker["id"])
if job:
    client.complete(job["id"], {"ok": True})
```
