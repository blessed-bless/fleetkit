import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { api } from "../api";
import { EmptyState } from "../components/EmptyState";
import { useI18n } from "../i18n";
import { ProjectPicker, useProject } from "../project";

export function WebhooksPage() {
  const { t } = useI18n();
  const { projectId } = useProject();
  const [apps, setApps] = useState<Awaited<ReturnType<typeof api.apps>>>([]);
  const [items, setItems] = useState<Awaited<ReturnType<typeof api.webhooks>>>([]);
  const [appId, setAppId] = useState("");
  const [name, setName] = useState("inbound");
  const [jobName, setJobName] = useState("webhook.received");
  const [msg, setMsg] = useState("");
  const [createdSecret, setCreatedSecret] = useState("");

  async function reload(id: string) {
    const [a, w] = await Promise.all([api.apps(id), api.webhooks(id)]);
    setApps(a);
    setItems(w);
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
      const wh = await api.createWebhook(projectId, appId, {
        name,
        target_job_name: jobName,
      });
      setCreatedSecret(wh.secret);
      setMsg(t("webhooks.created"));
      await reload(projectId);
    } catch (err) {
      setMsg(err instanceof Error ? err.message : t("webhooks.createFail"));
    }
  }

  const base = api.baseUrl;

  return (
    <div className="stack-gap">
      <div className="page-head">
        <div>
          <h1>{t("webhooks.title")}</h1>
          <p className="lead">{t("webhooks.lead")}</p>
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
          <label>{t("webhooks.name")}</label>
          <input value={name} onChange={(e) => setName(e.target.value)} required />
        </div>
        <div className="field">
          <label>{t("webhooks.targetJob")}</label>
          <input value={jobName} onChange={(e) => setJobName(e.target.value)} required />
        </div>
        <button className="btn" type="submit" disabled={!appId}>
          {t("webhooks.create")}
        </button>
      </form>
      {msg ? <p className="muted">{msg}</p> : null}
      {createdSecret ? (
        <section className="panel stack-gap">
          <p className="muted">{t("webhooks.secretHint")}</p>
          <pre className="log-box">{createdSecret}</pre>
        </section>
      ) : null}
      <section className="panel">
        {items.length === 0 ? (
          <EmptyState title={t("webhooks.empty")} hint={t("webhooks.lead")} />
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>{t("webhooks.name")}</th>
                <th>{t("webhooks.targetJob")}</th>
                <th>{t("webhooks.path")}</th>
                <th>{t("webhooks.status")}</th>
              </tr>
            </thead>
            <tbody>
              {items.map((w) => (
                <tr key={w.id}>
                  <td>{w.name}</td>
                  <td>
                    <code>{w.target_job_name}</code>
                  </td>
                  <td>
                    <code>
                      {base}
                      {w.ingest_path}
                    </code>
                  </td>
                  <td>
                    <span className={`badge ${w.is_enabled ? "ok" : "warn"}`}>
                      {w.is_enabled ? t("schedules.on") : t("schedules.off")}
                    </span>
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
