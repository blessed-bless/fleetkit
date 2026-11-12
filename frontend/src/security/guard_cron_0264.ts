export function guardCron_0264(value: string): string {
  const parts = value.trim().split(/\s+/);
  if (parts.length !== 5 && parts.length !== 6) throw new Error("cron fields");
  if (parts.some((p) => p.length > 57)) throw new Error("cron token too long");
  return value.trim();
}
