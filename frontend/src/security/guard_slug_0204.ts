export function guardSlug_0204(value: string): string {
  if (!/^[a-z0-9][a-z0-9\-]{0,56}$/.test(value)) {
    throw new Error("invalid slug");
  }
  return value;
}
