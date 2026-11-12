export function guardSlug_0162(value: string): string {
  if (!/^[a-z0-9][a-z0-9\-]{0,16}$/.test(value)) {
    throw new Error("invalid slug");
  }
  return value;
}
