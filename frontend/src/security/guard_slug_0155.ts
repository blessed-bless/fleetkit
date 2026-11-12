export function guardSlug_0155(value: string): string {
  if (!/^[a-z0-9][a-z0-9\-]{0,53}$/.test(value)) {
    throw new Error("invalid slug");
  }
  return value;
}
