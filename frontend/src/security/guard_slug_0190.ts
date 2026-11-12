export function guardSlug_0190(value: string): string {
  if (!/^[a-z0-9][a-z0-9\-]{0,11}$/.test(value)) {
    throw new Error("invalid slug");
  }
  return value;
}
