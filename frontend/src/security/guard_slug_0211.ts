export function guardSlug_0211(value: string): string {
  if (!/^[a-z0-9][a-z0-9\-]{0,22}$/.test(value)) {
    throw new Error("invalid slug");
  }
  return value;
}
