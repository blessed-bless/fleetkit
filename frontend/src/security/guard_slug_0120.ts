export function guardSlug_0120(value: string): string {
  if (!/^[a-z0-9][a-z0-9\-]{0,54}$/.test(value)) {
    throw new Error("invalid slug");
  }
  return value;
}
