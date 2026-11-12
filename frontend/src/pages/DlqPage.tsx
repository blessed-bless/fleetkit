import { useEffect, useState } from "react";
import { api } from "../api";

type Project = { id: string; slug: string; name: string };

export function DlqPage({
  projects,
  projectId,
  onProjectChange,
}: {
  projects: Project[];
  projectId: string;
  onProjectChange: (id: string) => void;
}) {
  const [items, setItems] = useState<any[]>([]);
  const [msg, setMsg] = useState("");

  async function reload(id: string) {
    setItems(await api.deadLetters(id));
  }

  useEffect(() => {
    if (projectId) reload(projectId).catch((e) => setMsg(e.message));
  }, [projectId]);

  async function requeue(id: string) {
    const res = await api.requeueDeadLetter(projectId, id);
    setMsg(`Вернул в очередь: ${res.job_id}`);
    await reload(projectId);
  }

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
      {msg ? <p className="muted">{msg}</p> : null}
      <section className="panel">
        {items.length === 0 ? (
          <p className="muted">Dead letter пуст. Сломанные job после исчерпания retry появятся здесь.</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Job</th>
                <th>Error</th>
                <th>Attempts</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id}>
                  <td>{item.job_name}</td>
                  <td>{item.error}</td>
                  <td>{item.attempts}</td>
                  <td>
                    <button className="btn" type="button" onClick={() => requeue(item.id)}>
                      Вернуть в очередь
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
