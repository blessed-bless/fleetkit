import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { api } from "../api";
import { useI18n } from "../i18n";

type Project = { id: string; slug: string; name: string };

export function SchedulesPage({
  projects,
  projectId,
  onProjectChange,
}: {
  projects: Project[];
  projectId: string;
  onProjectChange: (id: string) => void;
}) {
  const { t } = useI18n();
  const [apps, setApps] = useState<Awaited<ReturnType<typeof api.apps>>>([]);
  const [items, setItems] = useState<Awaited<ReturnType<typeof api.schedules>>>([]);
  const [appId, setAppId] = useState("");
  const [name, setName] = useState("heartbeat");
  const [cron, setCron] = useState("*/5 * * * *");
  const [msg, setMsg] = useState("");

  async function reload(id: string) {
    const [a, s] = await Promise.all([api.apps(id), api.schedules(id)]);
    setApps(a);
    setItems(s);
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
      await api.createSchedule(projectId, appId, { name, cron, payload: { source: "dashboard" } });
      setMsg(t("schedules.created"));
      await reload(projectId);
    } catch (err) {
      setMsg(err instanceof Error ? err.message : t("schedules.createFail"));
    }
  }

  async function toggle(id: string, enabled: boolean) {
    await api.patchSchedule(projectId, id, { is_enabled: !enabled });
    await reload(projectId);
    setMsg(enabled ? t("schedules.disabledMsg") : t("schedules.enabledMsg"));
  }

  return (
    <div className="stack-gap">
      <div className="page-head">
        <div>
          <h1>{t("schedules.title")}</h1>
          <p className="lead">{t("schedules.lead")}</p>
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
          <label>{t("schedules.name")}</label>
          <input value={name} onChange={(e) => setName(e.target.value)} required />
        </div>
        <div className="field">
          <label>{t("schedules.cron")}</label>
          <input value={cron} onChange={(e) => setCron(e.target.value)} required />
        </div>
        <button className="btn" type="submit" disabled={!appId}>
          {t("schedules.create")}
        </button>
      </form>
      {msg ? <p className="muted">{msg}</p> : null}
      <section className="panel">
        {items.length === 0 ? (
          <p className="muted">{t("schedules.empty")}</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>{t("schedules.name")}</th>
                <th>{t("schedules.cron")}</th>
                <th>{t("schedules.next")}</th>
                <th>{t("schedules.status")}</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {items.map((s) => (
                <tr key={s.id}>
                  <td>{s.name}</td>
                  <td>
                    <code>{s.cron}</code>
                  </td>
                  <td className="muted">
                    {s.next_run_at ? new Date(s.next_run_at).toLocaleString() : "—"}
                  </td>
                  <td>
                    <span className={`badge ${s.is_enabled ? "ok" : "warn"}`}>
                      {s.is_enabled ? t("schedules.on") : t("schedules.off")}
                    </span>
                  </td>
                  <td>
                    <button
                      className="btn ghost"
                      type="button"
                      onClick={() => toggle(s.id, s.is_enabled).catch((e) => setMsg(e.message))}
                    >
                      {s.is_enabled ? t("schedules.disable") : t("schedules.enable")}
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
