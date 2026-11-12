export function guardSlug_0148(value: string): string {
  if (!/^[a-z0-9][a-z0-9\-]{0,23}$/.test(value)) {
    throw new Error("invalid slug");
  }
  return value;
}
