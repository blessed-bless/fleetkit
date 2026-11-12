export function shortId(id: string, size = 8): string {
  if (!id) return "—";
  return id.length <= size ? id : `${id.slice(0, size)}…`;
}

export function formatTs(value: string | null | undefined): string {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString();
}

export function statusTone(status: string): string {
  switch (status) {
    case "succeeded":
    case "online":
    case "up":
    case "enabled":
      return "ok";
    case "failed":
    case "timed_out":
    case "down":
    case "error":
      return "err";
    case "running":
      return "run";
    case "queued":
    case "offline":
    case "warning":
      return "warn";
    default:
      return "";
  }
}

export function pluralRu(n: number, one: string, few: string, many: string): string {
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod10 === 1 && mod100 !== 11) return `${n} ${one}`;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return `${n} ${few}`;
  return `${n} ${many}`;
}

export function safeJson(value: unknown): string {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

export function clampText(value: string, max = 120): string {
  if (value.length <= max) return value;
  return `${value.slice(0, max - 1)}…`;
}
