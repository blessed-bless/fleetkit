import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { api } from "../api";
import { useI18n } from "../i18n";

type Project = { id: string; slug: string; name: string };

export function SecretsPage({
  projects,
  projectId,
  onProjectChange,
}: {
  projects: Project[];
  projectId: string;
  onProjectChange: (id: string) => void;
}) {
  const { t } = useI18n();
  const [items, setItems] = useState<any[]>([]);
  const [name, setName] = useState("BOT_TOKEN");
  const [value, setValue] = useState("");
  const [msg, setMsg] = useState("");
  const [revealed, setRevealed] = useState("");

  async function reload(id: string) {
    setItems(await api.secrets(id));
  }

  useEffect(() => {
    if (projectId) reload(projectId).catch((e) => setMsg(e.message));
  }, [projectId]);

  async function save(e: FormEvent) {
    e.preventDefault();
    await api.upsertSecret(projectId, { name, value, description: "" });
    setValue("");
    setMsg(t("secrets.saved"));
    await reload(projectId);
  }

  async function reveal(secretName: string) {
    const res = await api.revealSecret(projectId, secretName);
    setRevealed(`${res.name}=${res.value}`);
  }

  return (
    <div className="stack-gap">
      <div className="page-head">
        <div>
          <h1>{t("secrets.title")}</h1>
          <p className="lead">{t("secrets.lead")}</p>
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
      <form className="panel row" onSubmit={save}>
        <div className="field">
          <label>{t("secrets.name")}</label>
          <input value={name} onChange={(e) => setName(e.target.value)} required />
        </div>
        <div className="field">
          <label>{t("secrets.value")}</label>
          <input value={value} onChange={(e) => setValue(e.target.value)} required />
        </div>
        <button className="btn" type="submit">
          {t("secrets.save")}
        </button>
      </form>
      {msg ? <p className="muted">{msg}</p> : null}
      {revealed ? <pre className="log-box">{revealed}</pre> : null}
      <section className="panel">
        <table className="table">
          <thead>
            <tr>
              <th>{t("secrets.name")}</th>
              <th>{t("secrets.description")}</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id}>
                <td>{item.name}</td>
                <td>{item.description || "—"}</td>
                <td>
                  <button className="btn ghost" type="button" onClick={() => reveal(item.name)}>
                    {t("secrets.reveal")}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
