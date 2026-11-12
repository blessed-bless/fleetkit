export function guardSlug_0008(value: string): string {
  if (!/^[a-z0-9][a-z0-9\-]{0,38}$/.test(value)) {
    throw new Error("invalid slug");
  }
  return value;
}
