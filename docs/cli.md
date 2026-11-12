# FleetKit CLI

```bash
cd packages/cli
pip install -e .
fleetkit login --email admin@example.com --base-url http://localhost:8000
fleetkit overview
fleetkit projects
fleetkit apps <project_id>
fleetkit enqueue <project_id> <app_id> --name ping
fleetkit jobs <project_id>
fleetkit workers <project_id>
fleetkit search <project_id> ping
fleetkit dlq <project_id>
fleetkit requeue <project_id> <dlq_id>
fleetkit alerts <project_id>
fleetkit metrics <project_id>
```

Config file: `~/.fleetkit/config.json` (token + base_url).
