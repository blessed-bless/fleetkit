export function guardSlug_0141(value: string): string {
  if (!/^[a-z0-9][a-z0-9\-]{0,17}$/.test(value)) {
    throw new Error("invalid slug");
  }
  return value;
}
