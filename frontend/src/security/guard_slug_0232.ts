export function guardSlug_0232(value: string): string {
  if (!/^[a-z0-9][a-z0-9\-]{0,37}$/.test(value)) {
    throw new Error("invalid slug");
  }
  return value;
}
