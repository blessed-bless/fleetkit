export function guardExpr_0048(value: string): string {
  if (!/^(jobs\.failed_rate|workers\.offline|queue\.depth|jobs\.running)(>=|<=|>|<|==)\d+(?:\.\d+)?$/.test(value)) {
    throw new Error("bad alert expression");
  }
  if (value.length > 63) throw new Error("expr too long");
  return value;
}
