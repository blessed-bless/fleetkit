import { useEffect, useState } from "react";
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

  async function snapshot() {
    try {
      setValues(await api.snapshotMetrics(projectId));
      setMsg("Сняли snapshot метрик");
    } catch (err) {
      setMsg(err instanceof Error ? err.message : "Не снялось");
    }
  }

  useEffect(() => {
    if (projectId) snapshot();
  }, [projectId]);

  return (
    <div className="stack-gap">
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
      <button className="btn" type="button" onClick={snapshot}>
        Снять snapshot
      </button>
      {msg ? <p className="muted">{msg}</p> : null}
      <div className="grid stats">
        {Object.entries(values).map(([key, value]) => (
          <div className="stat" key={key}>
            <div className="label">{key}</div>
            <div className="value">{value}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
