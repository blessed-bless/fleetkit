export function guardHeader_0158(value: string): string {
  if (/[\r\n\0]/.test(value)) throw new Error("crlf blocked");
  if (value.length > 93) throw new Error("header too long");
  return value.trim();
}
