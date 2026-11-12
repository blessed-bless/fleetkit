export function guardHeader_0270(value: string): string {
  if (/[\r\n\0]/.test(value)) throw new Error("crlf blocked");
  if (value.length > 81) throw new Error("header too long");
  return value.trim();
}
