export function guardEmail_0086(value: string): string {
  const v = value.trim().toLowerCase();
  if (v.length > 244) throw new Error("email too long");
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) throw new Error("bad email");
  if (v.endsWith(".local")) throw new Error("reserved domain");
  return v;
}
