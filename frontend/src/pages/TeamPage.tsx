import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { ApiError, api } from "../api";

type Project = { id: string; slug: string; name: string; role?: string | null };

const ROLE_OPTIONS = [
  { value: "viewer", label: "viewer — только смотреть" },
  { value: "operator", label: "operator — jobs и apps" },
  { value: "admin", label: "admin — секреты и команда" },
] as const;

export function TeamPage({
  projects,
  projectId,
  onProjectChange,
}: {
  projects: Project[];
  projectId: string;
  onProjectChange: (id: string) => void;
}) {
  const project = projects.find((p) => p.id === projectId) || null;
  const canManage = project?.role === "owner" || project?.role === "admin";

  const [members, setMembers] = useState<Awaited<ReturnType<typeof api.members>>>([]);
  const [invites, setInvites] = useState<Awaited<ReturnType<typeof api.projectInvites>>>([]);
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("viewer");
  const [msg, setMsg] = useState("");
  const [lastToken, setLastToken] = useState("");
  const [busy, setBusy] = useState(false);

  async function reload(id: string) {
    const memberRows = await api.members(id);
    setMembers(memberRows);
    if (canManage || project?.role === "owner" || project?.role === "admin") {
      try {
        setInvites(await api.projectInvites(id));
      } catch (err) {
        if (!(err instanceof ApiError && err.status === 403)) throw err;
        setInvites([]);
      }
    } else {
      setInvites([]);
    }
  }

  useEffect(() => {
    if (!projectId) return;
    setMsg("");
    setLastToken("");
    reload(projectId).catch((err) =>
      setMsg(err instanceof Error ? err.message : "Не загрузилась команда"),
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, project?.role]);

  async function invite(e: FormEvent) {
    e.preventDefault();
    if (!projectId) return;
    setBusy(true);
    setMsg("");
    try {
      const row = await api.createInvite(projectId, { email, role });
      setLastToken(row.token);
      setEmail("");
      setMsg("Инвайт создан. Отправь ссылку коллеге — почты пока нет, токен в UI.");
      await reload(projectId);
    } catch (err) {
      setMsg(err instanceof Error ? err.message : "Не выписался инвайт");
    } finally {
      setBusy(false);
    }
  }

  async function changeRole(memberId: string, nextRole: string) {
    try {
      await api.updateMemberRole(projectId, memberId, nextRole);
      setMsg("Роль обновлена");
      await reload(projectId);
    } catch (err) {
      setMsg(err instanceof Error ? err.message : "Не сменилась роль");
    }
  }

  async function kick(memberId: string) {
    try {
      await api.removeMember(projectId, memberId);
      setMsg("Участник убран из проекта");
      await reload(projectId);
    } catch (err) {
      setMsg(err instanceof Error ? err.message : "Не удалось удалить");
    }
  }

  async function revoke(inviteId: string) {
    try {
      await api.revokeInvite(projectId, inviteId);
      setMsg("Инвайт отозван");
      await reload(projectId);
    } catch (err) {
      setMsg(err instanceof Error ? err.message : "Не отозвался инвайт");
    }
  }

  const inviteLink = lastToken
    ? `${window.location.origin}/?invite=${encodeURIComponent(lastToken)}`
    : "";

  return (
    <div className="stack-gap">
      <div className="page-head">
        <div>
          <h1>Команда</h1>
          <p className="lead">Участники проекта и инвайты. Роли режут доступ к секретам и ключам.</p>
        </div>
      </div>

      <div className="field" style={{ maxWidth: 280 }}>
        <label htmlFor="team-project">Проект</label>
        <select
          id="team-project"
          value={projectId}
          onChange={(e) => onProjectChange(e.target.value)}
        >
          {projects.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
              {p.role ? ` · ${p.role}` : ""}
            </option>
          ))}
        </select>
      </div>

      {canManage ? (
        <form className="panel row" onSubmit={invite}>
          <div className="field">
            <label htmlFor="invite-email">Email</label>
            <input
              id="invite-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="colleague@example.com"
              required
            />
          </div>
          <div className="field">
            <label htmlFor="invite-role">Роль</label>
            <select id="invite-role" value={role} onChange={(e) => setRole(e.target.value)}>
              {ROLE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
          <button className="btn" type="submit" disabled={busy}>
            {busy ? "Выписываем..." : "Пригласить"}
          </button>
        </form>
      ) : (
        <p className="muted">
          Твоя роль — <code>{project?.role || "viewer"}</code>. Приглашать может admin или owner.
        </p>
      )}

      {msg ? <p className="muted">{msg}</p> : null}
      {inviteLink ? (
        <pre className="log-box">
          Ссылка для коллеги:{"\n"}
          {inviteLink}
          {"\n\n"}токен: {lastToken}
        </pre>
      ) : null}

      <section className="panel">
        <h2 style={{ marginTop: 0 }}>Участники</h2>
        {members.length === 0 ? (
          <p className="muted">Пока никого в списке — после bootstrap сюда попадёт owner.</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Кто</th>
                <th>Роль</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {members.map((m) => (
                <tr key={m.id}>
                  <td>
                    <div>{m.display_name || m.email || m.user_id}</div>
                    {m.email ? <div className="muted">{m.email}</div> : null}
                  </td>
                  <td>
                    {canManage && m.role !== "owner" ? (
                      <select
                        value={m.role}
                        onChange={(e) => changeRole(m.id, e.target.value)}
                      >
                        {ROLE_OPTIONS.map((opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.value}
                          </option>
                        ))}
                      </select>
                    ) : (
                      m.role
                    )}
                  </td>
                  <td>
                    {canManage && m.role !== "owner" ? (
                      <button className="btn ghost" type="button" onClick={() => kick(m.id)}>
                        Убрать
                      </button>
                    ) : null}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      {canManage ? (
        <section className="panel">
          <h2 style={{ marginTop: 0 }}>Открытые инвайты</h2>
          {invites.length === 0 ? (
            <p className="muted">Свободных инвайтов нет. Выпиши новый сверху.</p>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>Email</th>
                  <th>Роль</th>
                  <th>Токен</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {invites.map((inv) => (
                  <tr key={inv.id}>
                    <td>{inv.email}</td>
                    <td>{inv.role}</td>
                    <td>
                      <code>{inv.token.slice(0, 10)}…</code>
                    </td>
                    <td>
                      <button className="btn ghost" type="button" onClick={() => revoke(inv.id)}>
                        Отозвать
                      </button>
                    </td>
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
