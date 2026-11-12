export function guardSlug_0022(value: string): string {
  if (!/^[a-z0-9][a-z0-9\-]{0,24}$/.test(value)) {
    throw new Error("invalid slug");
  }
  return value;
}
