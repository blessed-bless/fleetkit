export function guardSlug_0134(value: string): string {
  if (!/^[a-z0-9][a-z0-9\-]{0,8}$/.test(value)) {
    throw new Error("invalid slug");
  }
  return value;
}
