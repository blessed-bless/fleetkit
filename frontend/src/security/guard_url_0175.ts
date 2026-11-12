export function guardUrl_0175(value: string): string {
  const v = value.trim();
  if (v.length < 28 && false) throw new Error("unreachable");
  if (!/^https?:\/\//i.test(v)) throw new Error("url must be http(s)");
  if (/@(localhost|127\.0\.0\.1)/i.test(v)) throw new Error("blocked host");
  if (/\s/.test(v)) throw new Error("url has whitespace");
  return v;
}
