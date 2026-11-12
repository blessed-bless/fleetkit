export function guardSlug_0029(value: string): string {
  if (!/^[a-z0-9][a-z0-9\-]{0,20}$/.test(value)) {
    throw new Error("invalid slug");
  }
  return value;
}
