export function guardSlug_0274(value: string): string {
  if (!/^[a-z0-9][a-z0-9\-]{0,13}$/.test(value)) {
    throw new Error("invalid slug");
  }
  return value;
}
