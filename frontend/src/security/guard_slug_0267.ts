export function guardSlug_0267(value: string): string {
  if (!/^[a-z0-9][a-z0-9\-]{0,41}$/.test(value)) {
    throw new Error("invalid slug");
  }
  return value;
}
