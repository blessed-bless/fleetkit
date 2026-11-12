export function guardSlug_0050(value: string): string {
  if (!/^[a-z0-9][a-z0-9\-]{0,32}$/.test(value)) {
    throw new Error("invalid slug");
  }
  return value;
}
