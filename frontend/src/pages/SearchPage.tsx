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
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      setResult(await api.search(projectId, q));
      setMsg("");
    } catch (err) {
      setMsg(err instanceof Error ? err.message : "Поиск не удался");
    } finally {
      setBusy(false);
    }
  }

  const sections = result
    ? Object.entries(result).filter(([, v]) => Array.isArray(v) && (v as unknown[]).length > 0)
    : [];

  return (
    <div className="stack-gap">
      <div className="page-head">
        <div>
          <h1>Поиск</h1>
          <p className="lead">Apps, jobs, workers, events и dead letters в одном запросе.</p>
        </div>
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
      <form className="panel row" onSubmit={submit}>
        <div className="field">
          <label>Запрос</label>
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="ping, worker, error..."
          />
        </div>
        <button className="btn" type="submit" disabled={busy || !projectId}>
          {busy ? "Ищем..." : "Найти"}
        </button>
      </form>
      {msg ? <p className="error">{msg}</p> : null}
      {!result ? (
        <p className="muted">Введи фрагмент имени job или ошибку — покажем совпадения.</p>
      ) : sections.length === 0 ? (
        <p className="muted">Ничего не нашлось. Попробуй короче запрос или другой проект.</p>
      ) : (
        sections.map(([key, value]) => (
          <section className="panel stack-gap" key={key}>
            <h2>{key}</h2>
            <pre className="log-box">{JSON.stringify(value, null, 2)}</pre>
          </section>
        ))
      )}
    </div>
  );
}
