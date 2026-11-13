import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { api } from "../api";
import { EmptyState } from "../components/EmptyState";
import { useI18n } from "../i18n";
import { ProjectPicker, useProject } from "../project";

export function HealthPage() {
  const { t } = useI18n();
  const { projectId } = useProject();
  const [apps, setApps] = useState<Awaited<ReturnType<typeof api.apps>>>([]);
  const [items, setItems] = useState<Awaited<ReturnType<typeof api.healthChecks>>>([]);
  const [appId, setAppId] = useState("");
  const [name, setName] = useState("api-ping");
  const [target, setTarget] = useState("http://127.0.0.1:8000/healthz");
  const [msg, setMsg] = useState("");

  async function reload(id: string) {
    const [a, h] = await Promise.all([api.apps(id), api.healthChecks(id)]);
    setApps(a);
    setItems(h);
    if (a[0] && !appId) setAppId(a[0].id);
  }

  useEffect(() => {
    if (projectId) reload(projectId).catch((e) => setMsg(e.message));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  async function create(e: FormEvent) {
    e.preventDefault();
    if (!projectId || !appId) return;
    try {
      await api.createHealthCheck(projectId, {
        app_id: appId,
        name,
        kind: "http",
        target,
        interval_seconds: 60,
      });
      setMsg(t("health.created"));
      await reload(projectId);
    } catch (err) {
      setMsg(err instanceof Error ? err.message : t("health.createFail"));
    }
  }

  async function run(id: string) {
    if (!projectId) return;
    try {
      await api.runHealthCheck(projectId, id);
      setMsg(t("health.ran"));
      await reload(projectId);
    } catch (err) {
      setMsg(err instanceof Error ? err.message : t("health.runFail"));
    }
  }

  return (
    <div className="stack-gap">
      <div className="page-head">
        <div>
          <h1>{t("health.title")}</h1>
          <p className="lead">{t("health.lead")}</p>
        </div>
      </div>
      <ProjectPicker />
      <form className="panel row" onSubmit={create}>
        <div className="field">
          <label>{t("jobs.app")}</label>
          <select value={appId} onChange={(e) => setAppId(e.target.value)}>
            {apps.map((a) => (
              <option key={a.id} value={a.id}>
                {a.name}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label>{t("health.name")}</label>
          <input value={name} onChange={(e) => setName(e.target.value)} required />
        </div>
        <div className="field" style={{ minWidth: 280 }}>
          <label>{t("health.target")}</label>
          <input value={target} onChange={(e) => setTarget(e.target.value)} required />
        </div>
        <button className="btn" type="submit" disabled={!appId}>
          {t("health.create")}
        </button>
      </form>
      {msg ? <p className="muted">{msg}</p> : null}
      <section className="panel">
        {items.length === 0 ? (
          <EmptyState title={t("health.empty")} hint={t("health.emptyHint")} />
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>{t("health.name")}</th>
                <th>{t("health.target")}</th>
                <th>{t("health.status")}</th>
                <th>{t("health.checked")}</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {items.map((row) => (
                <tr key={row.id}>
                  <td>{row.name}</td>
                  <td>
                    <code>{row.target || "—"}</code>
                  </td>
                  <td>
                    <span
                      className={`badge ${
                        row.last_status === "ok"
                          ? "ok"
                          : row.last_status === "fail"
                            ? "err"
                            : "warn"
                      }`}
                    >
                      {row.last_status || "—"}
                    </span>
                    {row.last_error ? (
                      <div className="muted" style={{ fontSize: "0.8rem" }}>
                        {row.last_error}
                      </div>
                    ) : null}
                  </td>
                  <td className="muted">
                    {row.last_checked_at
                      ? new Date(row.last_checked_at).toLocaleString()
                      : t("health.never")}
                  </td>
                  <td>
                    <button className="btn ghost" type="button" onClick={() => run(row.id)}>
                      {t("health.run")}
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
