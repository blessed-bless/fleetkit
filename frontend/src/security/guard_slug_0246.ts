export function guardSlug_0246(value: string): string {
  if (!/^[a-z0-9][a-z0-9\-]{0,43}$/.test(value)) {
    throw new Error("invalid slug");
  }
  return value;
}
