export function guardSlug_0218(value: string): string {
  if (!/^[a-z0-9][a-z0-9\-]{0,21}$/.test(value)) {
    throw new Error("invalid slug");
  }
  return value;
}
