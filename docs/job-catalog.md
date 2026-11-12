# Built-in job catalog

| Job name | Purpose | Payload highlights |
|----------|---------|--------------------|
| `ping` | Connectivity check | any |
| `system.info` | Runtime fingerprint | — |
| `http.fetch` | HTTP request | `url`, `method`, `headers`, `body`, `timeout` |
| `http.json` | GET JSON | `url` |
| `util.sleep` | Delay (cap 60s) | `seconds` |
| `util.hash` | Hash text | `text`, `algo` |
| `util.json.validate` | Parse JSON | `raw` |
| `notify.echo` | Echo payload | any |
| `transform.map_keys` | Rename keys | `mapping`, `data` |
| `transform.filter_keys` | Keep keys | `keys`, `data` |
| `batch.split` | Chunk list | `items`, `size` |
| `demo.fail` | Always fail | `message` |
| `demo.flaky` | Fail until N | `attempt`, `succeed_after` |
| `telegram.send_text` | Send TG message | `bot_token`, `chat_id`, `text` |
| `cron.heartbeat` | Schedule pulse | `_schedule_id` |
| `webhook.received` | Ingest wrapper | webhook body |
| `schedule.*` | Generic cron handler | schedule payload |
| `demo.prefix.01` … `demo.prefix.40` | Catalog fillers / load tests | any |

## Agent tips

1. Prefer small payloads; put blobs in object storage and pass URLs.
2. Write progress with `/agent/jobs/{id}/logs`.
3. Emit custom metrics with `/agent/metrics`.
4. After max attempts FleetKit pushes the job into DLQ.
