export function guardSlug_0043(value: string): string {
  if (!/^[a-z0-9][a-z0-9\-]{0,50}$/.test(value)) {
    throw new Error("invalid slug");
  }
  return value;
}
