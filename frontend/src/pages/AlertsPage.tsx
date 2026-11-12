import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { api } from "../api";
import { useI18n } from "../i18n";

type Project = { id: string; slug: string; name: string };

export function AlertsPage({
  projects,
  projectId,
  onProjectChange,
}: {
  projects: Project[];
  projectId: string;
  onProjectChange: (id: string) => void;
}) {
  const { t } = useI18n();
  const [rules, setRules] = useState<any[]>([]);
  const [fires, setFires] = useState<any[]>([]);
  const [name, setName] = useState("Queue too deep");
  const [expression, setExpression] = useState("queue.depth>20");
  const [msg, setMsg] = useState("");

  async function reload(id: string) {
    const [r, f] = await Promise.all([api.alertRules(id), api.alertFires(id)]);
    setRules(r);
    setFires(f);
  }

  useEffect(() => {
    if (projectId) reload(projectId).catch((e) => setMsg(e.message));
  }, [projectId]);

  async function create(e: FormEvent) {
    e.preventDefault();
    await api.createAlertRule(projectId, { name, expression, severity: "warning" });
    setMsg(t("alerts.added"));
    await reload(projectId);
  }

  async function evaluate() {
    const res = await api.evaluateAlerts(projectId);
    setMsg(t("alerts.fired", { n: res.fired }));
    await reload(projectId);
  }

  return (
    <div className="stack-gap">
      <div className="page-head">
        <div>
          <h1>{t("alerts.title")}</h1>
          <p className="lead">{t("alerts.lead")}</p>
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
      <form className="panel row" onSubmit={create}>
        <div className="field">
          <label>{t("alerts.name")}</label>
          <input value={name} onChange={(e) => setName(e.target.value)} required />
        </div>
        <div className="field">
          <label>{t("alerts.expr")}</label>
          <input value={expression} onChange={(e) => setExpression(e.target.value)} required />
        </div>
        <button className="btn" type="submit">
          {t("alerts.add")}
        </button>
        <button className="btn ghost" type="button" onClick={evaluate}>
          {t("alerts.checkNow")}
        </button>
      </form>
      {msg ? <p className="muted">{msg}</p> : null}
      <section className="panel">
        <h2>{t("alerts.rules")}</h2>
        <table className="table">
          <thead>
            <tr>
              <th>{t("alerts.name")}</th>
              <th>{t("alerts.expr")}</th>
              <th>{t("alerts.severity")}</th>
            </tr>
          </thead>
          <tbody>
            {rules.map((r) => (
              <tr key={r.id}>
                <td>{r.name}</td>
                <td>{r.expression}</td>
                <td>{r.severity}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      <section className="panel">
        <h2>{t("alerts.fires")}</h2>
        {fires.length === 0 ? (
          <p className="muted">{t("alerts.firesEmpty")}</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>{t("alerts.when")}</th>
                <th>{t("alerts.message")}</th>
              </tr>
            </thead>
            <tbody>
              {fires.map((f) => (
                <tr key={f.id}>
                  <td className="muted">{new Date(f.created_at).toLocaleString()}</td>
                  <td>{f.message}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
