export function guardSlug_0015(value: string): string {
  if (!/^[a-z0-9][a-z0-9\-]{0,34}$/.test(value)) {
    throw new Error("invalid slug");
  }
  return value;
}
