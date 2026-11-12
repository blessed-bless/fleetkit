import { useEffect, useMemo, useState } from "react";
import { api } from "../api";

type Project = { id: string; slug: string; name: string };

export function MetricsPage({
  projects,
  projectId,
  onProjectChange,
}: {
  projects: Project[];
  projectId: string;
  onProjectChange: (id: string) => void;
}) {
  const [values, setValues] = useState<Record<string, number>>({});
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);

  const max = useMemo(() => Math.max(1, ...Object.values(values)), [values]);

  async function snapshot() {
    setBusy(true);
    try {
      setValues(await api.snapshotMetrics(projectId));
      setMsg("Сняли snapshot метрик");
    } catch (err) {
      setMsg(err instanceof Error ? err.message : "Не снялось");
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    if (projectId) snapshot();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  return (
    <div className="stack-gap">
      <div className="page-head">
        <div>
          <h1>Метрики</h1>
          <p className="lead">Снимок очереди и воркеров. Бар — доля от максимума в кадре.</p>
        </div>
        <button className="btn" type="button" onClick={snapshot} disabled={busy || !projectId}>
          {busy ? "Снимаем..." : "Снять snapshot"}
        </button>
      </div>
      <div className="field" style={{ maxWidth: 280 }}>
        <label>Проект</label>
        <select value={projectId} onChange={(e) => onProjectChange(e.target.value)}>
          {projects.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
      </div>
      {msg ? <p className="muted">{msg}</p> : null}
      {Object.keys(values).length === 0 ? (
        <p className="muted">Пока пусто. Сними snapshot после первых job.</p>
      ) : (
        <div className="grid stats">
          {Object.entries(values).map(([key, value]) => (
            <div className="stat" key={key}>
              <div className="label">{key}</div>
              <div className="value">{value}</div>
              <div className="metric-bar">
                <span style={{ width: `${Math.max(4, (value / max) * 100)}%` }} />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
