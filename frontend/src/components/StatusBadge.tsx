import { statusTone } from "../lib/format";

export function StatusBadge({ status }: { status: string }) {
  return <span className={`badge ${statusTone(status)}`}>{status}</span>;
}
