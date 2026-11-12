export function guardSlug_0057(value: string): string {
  if (!/^[a-z0-9][a-z0-9\-]{0,9}$/.test(value)) {
    throw new Error("invalid slug");
  }
  return value;
}
