import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { api } from "../api";
import { useI18n } from "../i18n";
import { ProjectPicker, useProject } from "../project";

export function SettingsPage() {
  const { t } = useI18n();
  const { projectId, reload } = useProject();
  const [secret, setSecret] = useState("");
  const [keys, setKeys] = useState<Awaited<ReturnType<typeof api.apiKeys>>>([]);
  const [projName, setProjName] = useState("");
  const [projSlug, setProjSlug] = useState("");
  const [msg, setMsg] = useState("");

  useEffect(() => {
    if (!projectId) return;
    api.apiKeys(projectId).then(setKeys).catch((e) => setMsg(e.message));
  }, [projectId, secret]);

  async function mint() {
    if (!projectId) return;
    try {
      const key = await api.createApiKey(projectId, `key-${Date.now()}`);
      setSecret(key.secret);
      setMsg(t("settings.minted"));
    } catch (err) {
      setMsg(err instanceof Error ? err.message : t("settings.mintFail"));
    }
  }

  async function createProject(e: FormEvent) {
    e.preventDefault();
    try {
      await api.createProject({ name: projName, slug: projSlug });
      setProjName("");
      setProjSlug("");
      setMsg(t("settings.projectCreated"));
      await reload();
    } catch (err) {
      setMsg(err instanceof Error ? err.message : t("settings.projectFail"));
    }
  }

  return (
    <div className="stack-gap">
      <div className="page-head">
        <div>
          <h1>{t("settings.title")}</h1>
          <p className="lead">{t("settings.lead")}</p>
        </div>
      </div>
      <ProjectPicker />
      <section className="panel stack-gap">
        <h2 style={{ margin: 0 }}>{t("settings.newProject")}</h2>
        <form className="row" onSubmit={createProject}>
          <div className="field">
            <label>{t("apps.name")}</label>
            <input value={projName} onChange={(e) => setProjName(e.target.value)} required />
          </div>
          <div className="field">
            <label>{t("apps.slug")}</label>
            <input
              value={projSlug}
              onChange={(e) => setProjSlug(e.target.value)}
              pattern="^[a-z0-9][a-z0-9\-]*$"
              required
            />
          </div>
          <button className="btn" type="submit">
            {t("settings.createProject")}
          </button>
        </form>
      </section>
      <section className="panel stack-gap">
        <p className="muted">{t("settings.hint")}</p>
        <button className="btn" type="button" onClick={mint}>
          {t("settings.mint")}
        </button>
        {msg ? <p className="muted">{msg}</p> : null}
        {secret ? <pre className="log-box">{secret}</pre> : null}
        {keys.length === 0 ? (
          <p className="muted">{t("settings.keysEmpty")}</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>{t("apps.name")}</th>
                <th>prefix</th>
                <th>{t("overview.when")}</th>
              </tr>
            </thead>
            <tbody>
              {keys.map((k) => (
                <tr key={k.id}>
                  <td>{k.name}</td>
                  <td>
                    <code>{k.key_prefix}</code>
                  </td>
                  <td className="muted">{new Date(k.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
