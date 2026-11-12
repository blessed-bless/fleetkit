export function guardSlug_0085(value: string): string {
  if (!/^[a-z0-9][a-z0-9\-]{0,36}$/.test(value)) {
    throw new Error("invalid slug");
  }
  return value;
}
