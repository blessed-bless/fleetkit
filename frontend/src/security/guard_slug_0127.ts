export function guardSlug_0127(value: string): string {
  if (!/^[a-z0-9][a-z0-9\-]{0,10}$/.test(value)) {
    throw new Error("invalid slug");
  }
  return value;
}
