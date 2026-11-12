export function guardSlug_0225(value: string): string {
  if (!/^[a-z0-9][a-z0-9\-]{0,49}$/.test(value)) {
    throw new Error("invalid slug");
  }
  return value;
}
