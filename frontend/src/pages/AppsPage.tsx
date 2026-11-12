import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { api } from "../api";
import { EmptyState } from "../components/EmptyState";
import { useI18n } from "../i18n";
import { ProjectPicker, useProject } from "../project";

export function AppsPage() {
  const { t } = useI18n();
  const { projectId, error } = useProject();
  const [apps, setApps] = useState<Awaited<ReturnType<typeof api.apps>>>([]);
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [kind, setKind] = useState("worker");
  const [msg, setMsg] = useState("");
  const [selectedApp, setSelectedApp] = useState("");
  const [envRows, setEnvRows] = useState<Awaited<ReturnType<typeof api.appEnv>>>([]);
  const [envKey, setEnvKey] = useState("LOG_LEVEL");
  const [envValue, setEnvValue] = useState("info");
  const [envSecret, setEnvSecret] = useState(false);

  async function reload(id: string) {
    const list = await api.apps(id);
    setApps(list);
    if (list[0] && !selectedApp) setSelectedApp(list[0].id);
  }

  async function reloadEnv(appId: string) {
    if (!projectId || !appId) return;
    setEnvRows(await api.appEnv(projectId, appId));
  }

  useEffect(() => {
    if (projectId) reload(projectId).catch((err) => setMsg(err.message));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  useEffect(() => {
    if (selectedApp) reloadEnv(selectedApp).catch((err) => setMsg(err.message));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedApp, projectId]);

  async function create(e: FormEvent) {
    e.preventDefault();
    if (!projectId) return;
    setMsg("");
    try {
      await api.createApp(projectId, { name, slug, kind });
      setName("");
      setSlug("");
      await reload(projectId);
      setMsg(t("apps.created"));
    } catch (err) {
      setMsg(err instanceof Error ? err.message : t("apps.createFail"));
    }
  }

  async function toggle(appId: string, enabled: boolean) {
    if (!projectId) return;
    try {
      await api.patchApp(projectId, appId, { is_enabled: !enabled });
      await reload(projectId);
      setMsg(!enabled ? t("apps.enabledMsg") : t("apps.disabledMsg"));
    } catch (err) {
      setMsg(err instanceof Error ? err.message : t("apps.toggleFail"));
    }
  }

  return (
    <div className="stack-gap">
      <div className="page-head">
        <div>
          <h1>{t("apps.title")}</h1>
          <p className="lead">{t("apps.lead")}</p>
        </div>
      </div>
      {error ? <p className="error">{error}</p> : null}
      <ProjectPicker />
      <form className="panel row" onSubmit={create}>
        <div className="field">
          <label>{t("apps.name")}</label>
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
          <label>{t("apps.kind")}</label>
          <select value={kind} onChange={(e) => setKind(e.target.value)}>
            <option value="worker">worker</option>
            <option value="bot">bot</option>
            <option value="cron">cron</option>
            <option value="webhook">webhook</option>
          </select>
        </div>
        <button className="btn" type="submit">
          {t("apps.create")}
        </button>
      </form>
      {msg ? <p className="muted">{msg}</p> : null}
      <section className="panel">
        {apps.length === 0 ? (
          <EmptyState title={t("apps.empty")} hint={t("apps.emptyHint")} />
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>{t("apps.name")}</th>
                <th>{t("apps.slug")}</th>
                <th>{t("apps.kind")}</th>
                <th>{t("apps.status")}</th>
                <th />
                <th>ID</th>
              </tr>
            </thead>
            <tbody>
              {apps.map((app) => (
                <tr
                  key={app.id}
                  className={selectedApp === app.id ? "selected" : ""}
                  onClick={() => setSelectedApp(app.id)}
                  style={{ cursor: "pointer" }}
                >
                  <td>{app.name}</td>
                  <td>{app.slug}</td>
                  <td>{app.kind}</td>
                  <td>
                    <span className={`badge ${app.is_enabled ? "ok" : "warn"}`}>
                      {app.is_enabled ? t("apps.enabled") : t("apps.disabled")}
                    </span>
                  </td>
                  <td>
                    <button
                      className="btn ghost"
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        toggle(app.id, app.is_enabled);
                      }}
                    >
                      {app.is_enabled ? t("apps.disable") : t("apps.enable")}
                    </button>
                  </td>
                  <td className="muted">{app.id}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
      {selectedApp ? (
        <section className="panel stack-gap">
          <h2 style={{ margin: 0 }}>{t("apps.envTitle")}</h2>
          <form
            className="row"
            onSubmit={async (e) => {
              e.preventDefault();
              if (!projectId || !selectedApp) return;
              try {
                await api.upsertAppEnv(projectId, selectedApp, {
                  key: envKey,
                  value: envValue,
                  is_secret: envSecret,
                });
                setMsg(t("apps.envSaved"));
                setEnvValue("");
                await reloadEnv(selectedApp);
              } catch (err) {
                setMsg(err instanceof Error ? err.message : t("apps.envFail"));
              }
            }}
          >
            <div className="field">
              <label>{t("apps.envKey")}</label>
              <input
                value={envKey}
                onChange={(e) => setEnvKey(e.target.value)}
                pattern="^[A-Z][A-Z0-9_]*$"
                required
              />
            </div>
            <div className="field">
              <label>{t("apps.envValue")}</label>
              <input value={envValue} onChange={(e) => setEnvValue(e.target.value)} required />
            </div>
            <label className="field" style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
              <input
                type="checkbox"
                checked={envSecret}
                onChange={(e) => setEnvSecret(e.target.checked)}
              />
              {t("apps.envSecret")}
            </label>
            <button className="btn" type="submit">
              {t("apps.envSave")}
            </button>
          </form>
          {envRows.length === 0 ? (
            <p className="muted">{t("apps.envEmpty")}</p>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>{t("apps.envKey")}</th>
                  <th>{t("apps.envValue")}</th>
                </tr>
              </thead>
              <tbody>
                {envRows.map((row) => (
                  <tr key={row.id}>
                    <td>
                      <code>{row.key}</code>
                    </td>
                    <td className="muted">{row.value_preview}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      ) : null}
    </div>
  );
}
