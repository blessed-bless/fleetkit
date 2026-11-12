import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { api } from "../api";
import { EmptyState } from "../components/EmptyState";
import { useI18n } from "../i18n";
import { ProjectPicker, useProject } from "../project";

export function TemplatesPage() {
  const { t } = useI18n();
  const { projectId } = useProject();
  const [apps, setApps] = useState<Awaited<ReturnType<typeof api.apps>>>([]);
  const [items, setItems] = useState<Awaited<ReturnType<typeof api.templates>>>([]);
  const [appId, setAppId] = useState("");
  const [name, setName] = useState("Ping");
  const [slug, setSlug] = useState("ping");
  const [jobName, setJobName] = useState("ping");
  const [msg, setMsg] = useState("");

  async function reload(id: string) {
    const [a, rows] = await Promise.all([api.apps(id), api.templates(id)]);
    setApps(a);
    setItems(rows);
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
      await api.createTemplate(projectId, {
        app_id: appId,
        slug,
        name,
        job_name: jobName,
        payload: {},
      });
      setMsg(t("templates.created"));
      await reload(projectId);
    } catch (err) {
      setMsg(err instanceof Error ? err.message : t("templates.createFail"));
    }
  }

  async function run(id: string) {
    if (!projectId) return;
    try {
      const res = await api.runTemplate(projectId, id);
      setMsg(t("templates.ran", { id: res.job_id }));
      await reload(projectId);
    } catch (err) {
      setMsg(err instanceof Error ? err.message : t("templates.runFail"));
    }
  }

  return (
    <div className="stack-gap">
      <div className="page-head">
        <div>
          <h1>{t("templates.title")}</h1>
          <p className="lead">{t("templates.lead")}</p>
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
          <label>{t("templates.name")}</label>
          <input value={name} onChange={(e) => setName(e.target.value)} required />
        </div>
        <div className="field">
          <label>{t("apps.slug")}</label>
          <input
            value={slug}
            onChange={(e) => setSlug(e.target.value)}
            pattern="^[a-z0-9][a-z0-9\-]*$"
            required
          />
        </div>
        <div className="field">
          <label>{t("jobs.name")}</label>
          <input value={jobName} onChange={(e) => setJobName(e.target.value)} required />
        </div>
        <button className="btn" type="submit" disabled={!appId}>
          {t("templates.create")}
        </button>
      </form>
      {msg ? <p className="muted">{msg}</p> : null}
      <section className="panel">
        {items.length === 0 ? (
          <EmptyState title={t("templates.empty")} hint={t("templates.emptyHint")} />
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>{t("templates.name")}</th>
                <th>{t("apps.slug")}</th>
                <th>{t("jobs.name")}</th>
                <th>{t("jobs.queue")}</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {items.map((row) => (
                <tr key={row.id}>
                  <td>{row.name}</td>
                  <td>
                    <code>{row.slug}</code>
                  </td>
                  <td>
                    <code>{row.job_name}</code>
                  </td>
                  <td>{row.queue}</td>
                  <td>
                    <button className="btn ghost" type="button" onClick={() => run(row.id)}>
                      {t("templates.run")}
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
