import { useState } from "react";
import type { FormEvent } from "react";
import { api } from "../api";
import { useI18n } from "../i18n";

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
  const { t } = useI18n();
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
      setMsg(err instanceof Error ? err.message : t("search.fail"));
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
          <h1>{t("search.title")}</h1>
          <p className="lead">{t("search.lead")}</p>
        </div>
      </div>
      <div className="field" style={{ maxWidth: 280 }}>
        <label>{t("project.label")}</label>
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
          <label>{t("search.query")}</label>
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="ping, worker, error..."
          />
        </div>
        <button className="btn" type="submit" disabled={busy || !projectId}>
          {busy ? t("search.searching") : t("search.submit")}
        </button>
      </form>
      {msg ? <p className="error">{msg}</p> : null}
      {!result ? (
        <p className="muted">{t("search.hint")}</p>
      ) : sections.length === 0 ? (
        <p className="muted">{t("search.empty")}</p>
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
