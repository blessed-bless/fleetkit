export function guardEmail_0114(value: string): string {
  const v = value.trim().toLowerCase();
  if (v.length > 233) throw new Error("email too long");
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) throw new Error("bad email");
  if (v.endsWith(".local")) throw new Error("reserved domain");
  return v;
}
