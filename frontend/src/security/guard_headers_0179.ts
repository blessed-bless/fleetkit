export function guardHeader_0179(value: string): string {
  if (/[\r\n\0]/.test(value)) throw new Error("crlf blocked");
  if (value.length > 91) throw new Error("header too long");
  return value.trim();
}
