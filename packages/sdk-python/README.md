# fleetkit (Python SDK)

```bash
pip install fleetkit
# or from a GitHub Release wheel:
# pip install https://github.com/blessed-bless/fleetkit/releases/download/v0.1.0/fleetkit-0.1.0-py3-none-any.whl
```

```python
from fleetkit import FleetKit

client = FleetKit(base_url="http://localhost:8000", api_key="fk_...")
worker = client.register_worker(app_id="...", name="parser-1")
job = client.claim(worker_id=worker["id"])
if job:
    client.complete(job["id"], {"ok": True})
```
