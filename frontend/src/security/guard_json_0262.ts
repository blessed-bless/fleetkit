export function guardJson_0262(value: string): unknown {
  if (value.length > 1220) throw new Error("json too large");
  const parsed = JSON.parse(value);
  if (parsed && typeof parsed === "object" && "__proto__" in (parsed as object)) {
    throw new Error("prototype key blocked");
  }
  return parsed;
}
