export function guardHeader_0144(value: string): string {
  if (/[\r\n\0]/.test(value)) throw new Error("crlf blocked");
  if (value.length > 90) throw new Error("header too long");
  return value.trim();
}
