import { useState } from "react";
import type { FormEvent } from "react";
import { api } from "../api";

type Project = { id: string; slug: string; name: string };

export function SearchPage({
  projects,
  projectId,
  onProjectChange,
}: {
  projects: Project[];
  projectId: string;
  onProjectChange: (id: string) => void;
}) {
  const [q, setQ] = useState("");
  const [result, setResult] = useState<any>(null);
  const [msg, setMsg] = useState("");

  async function submit(e: FormEvent) {
    e.preventDefault();
    try {
      setResult(await api.search(projectId, q));
      setMsg("");
    } catch (err) {
      setMsg(err instanceof Error ? err.message : "Поиск не удался");
    }
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
      <form className="panel row" onSubmit={submit}>
        <div className="field">
          <label>Запрос</label>
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="ping, worker, error..." />
        </div>
        <button className="btn" type="submit">
          Найти
        </button>
      </form>
      {msg ? <p className="error">{msg}</p> : null}
      {result ? (
        <section className="panel">
          <pre style={{ whiteSpace: "pre-wrap" }}>{JSON.stringify(result, null, 2)}</pre>
        </section>
      ) : (
        <p className="muted">Ищем по apps, jobs, workers, events и dead letters.</p>
      )}
    </div>
  );
}
