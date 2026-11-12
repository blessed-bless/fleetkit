export function guardSlug_0001(value: string): string {
  if (!/^[a-z0-9][a-z0-9\-]{0,19}$/.test(value)) {
    throw new Error("invalid slug");
  }
  return value;
}
