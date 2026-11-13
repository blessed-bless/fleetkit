import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { ApiError, api } from "../api";

type Project = { id: string; slug: string; name: string; role?: string | null };

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

  const canWrite = projectId
    ? ["owner", "admin"].includes(projects.find((p) => p.id === projectId)?.role || "owner")
    : false;

  async function reload(id: string) {
    setItems(await api.secrets(id));
  }

  useEffect(() => {
    if (!projectId) return;
    reload(projectId).catch((e) => {
      if (e instanceof ApiError && e.status === 403) {
        setItems([]);
        setMsg("У твоей роли нет доступа к списку секретов (нужен admin/owner).");
        return;
      }
      setMsg(e.message);
    });
  }, [projectId]);

  async function save(e: FormEvent) {
    e.preventDefault();
    try {
      await api.upsertSecret(projectId, { name, value, description: "" });
      setValue("");
      setMsg("Секрет сохранён");
      await reload(projectId);
    } catch (err) {
      setMsg(err instanceof Error ? err.message : "Не сохранился секрет");
    }
  }

  async function reveal(secretName: string) {
    try {
      const res = await api.revealSecret(projectId, secretName);
      setRevealed(`${res.name}=${res.value}`);
    } catch (err) {
      setMsg(err instanceof Error ? err.message : "Reveal недоступен для твоей роли");
    }
  }

  return (
    <div className="stack-gap">
      <div className="page-head">
        <div>
          <h1>Секреты</h1>
          <p className="lead">Токены ботов и ключи для воркеров. Reveal — только по клику.</p>
        </div>
      </div>
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
      {canWrite ? (
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
      ) : null}
      {msg ? <p className="muted">{msg}</p> : null}
      {revealed ? <pre className="log-box">{revealed}</pre> : null}
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
