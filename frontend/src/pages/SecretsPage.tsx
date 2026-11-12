import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { api } from "../api";

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
    setMsg("Секрет сохранён");
    await reload(projectId);
  }

  async function reveal(secretName: string) {
    const res = await api.revealSecret(projectId, secretName);
    setRevealed(`${res.name}=${res.value}`);
  }

  return (
    <div className="stack-gap">
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
      <form className="panel row" onSubmit={save}>
        <div className="field">
          <label>Имя</label>
          <input value={name} onChange={(e) => setName(e.target.value)} required />
        </div>
        <div className="field">
          <label>Значение</label>
          <input value={value} onChange={(e) => setValue(e.target.value)} required />
        </div>
        <button className="btn" type="submit">
          Сохранить секрет
        </button>
      </form>
      {msg ? <p className="muted">{msg}</p> : null}
      {revealed ? <pre style={{ padding: 12 }}>{revealed}</pre> : null}
      <section className="panel">
        <table className="table">
          <thead>
            <tr>
              <th>Имя</th>
              <th>Описание</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id}>
                <td>{item.name}</td>
                <td>{item.description || "—"}</td>
                <td>
                  <button className="btn ghost" type="button" onClick={() => reveal(item.name)}>
                    Показать
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
