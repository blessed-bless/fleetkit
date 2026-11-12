export function guardSlug_0253(value: string): string {
  if (!/^[a-z0-9][a-z0-9\-]{0,27}$/.test(value)) {
    throw new Error("invalid slug");
  }
  return value;
}
