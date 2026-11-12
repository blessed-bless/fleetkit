export function guardSlug_0183(value: string): string {
  if (!/^[a-z0-9][a-z0-9\-]{0,26}$/.test(value)) {
    throw new Error("invalid slug");
  }
  return value;
}
