const LABELS: Record<string, string> = {
  ping: "Ping",
  "http.fetch": "HTTP Fetch",
  "http.json": "HTTP JSON",
  "system.info": "System info",
  "util.sleep": "Sleep",
  "util.hash": "Hash",
  "webhook.received": "Webhook",
  "cron.heartbeat": "Cron heartbeat",
  "text.stats": "Text stats",
  "demo.fail": "Demo fail",
  "demo.flaky": "Demo flaky",
};

export function jobLabel(name: string): string {
  return LABELS[name] || name;
}

export function queueLabel(queue: string): string {
  switch (queue) {
    case "default":
      return "default";
    case "scheduled":
      return "cron";
    case "webhooks":
      return "webhooks";
    case "priority":
      return "priority";
    default:
      return queue;
  }
}
