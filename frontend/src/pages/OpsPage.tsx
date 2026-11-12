import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { api } from "../api";
import { EmptyState } from "../components/EmptyState";
import { useI18n } from "../i18n";
import { ProjectPicker, useProject } from "../project";

export function OpsPage() {
  const { t } = useI18n();
  const { projectId } = useProject();
  const [retention, setRetention] = useState<Awaited<ReturnType<typeof api.retention>>>([]);
  const [flags, setFlags] = useState<Awaited<ReturnType<typeof api.flags>>>([]);
  const [members, setMembers] = useState<Awaited<ReturnType<typeof api.members>>>([]);
  const [flagKey, setFlagKey] = useState("beta.ui");
  const [flagOn, setFlagOn] = useState(false);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteToken, setInviteToken] = useState("");
  const [msg, setMsg] = useState("");

  async function reload(id: string) {
    const [r, f, m] = await Promise.all([api.retention(id), api.flags(id), api.members(id)]);
    setRetention(r);
    setFlags(f);
    setMembers(m);
  }

  useEffect(() => {
    if (projectId) reload(projectId).catch((e) => setMsg(e.message));
  }, [projectId]);

  async function saveRetention(kind: string, keepDays: number, enabled: boolean) {
    if (!projectId) return;
    try {
      await api.patchRetention(projectId, kind, { keep_days: keepDays, is_enabled: enabled });
      setMsg(t("ops.retentionSaved"));
      await reload(projectId);
    } catch (err) {
      setMsg(err instanceof Error ? err.message : t("ops.retentionFail"));
    }
  }

  async function runNow() {
    if (!projectId) return;
    try {
      const res = await api.runRetention(projectId);
      const total = Object.values(res).reduce((a, b) => a + b, 0);
      setMsg(t("ops.retentionRan", { n: total }));
      await reload(projectId);
    } catch (err) {
      setMsg(err instanceof Error ? err.message : t("ops.retentionFail"));
    }
  }

  async function upsertFlag(e: FormEvent) {
    e.preventDefault();
    if (!projectId) return;
    try {
      await api.upsertFlag(projectId, { key: flagKey, enabled: flagOn });
      setMsg(t("ops.flagSaved"));
      await reload(projectId);
    } catch (err) {
      setMsg(err instanceof Error ? err.message : t("ops.flagFail"));
    }
  }

  return (
    <div className="stack-gap">
      <div className="page-head">
        <div>
          <h1>{t("ops.title")}</h1>
          <p className="lead">{t("ops.lead")}</p>
        </div>
      </div>
      <ProjectPicker />
      {msg ? <p className="muted">{msg}</p> : null}

      <section className="panel stack-gap">
        <div className="page-head" style={{ marginBottom: 0 }}>
          <h2 style={{ margin: 0 }}>{t("ops.retention")}</h2>
          <button className="btn ghost" type="button" onClick={runNow}>
            {t("ops.runRetention")}
          </button>
        </div>
        {retention.length === 0 ? (
          <EmptyState title={t("ops.retentionEmpty")} hint={t("ops.retentionHint")} />
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>{t("ops.kind")}</th>
                <th>{t("ops.keepDays")}</th>
                <th>{t("ops.enabled")}</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {retention.map((row) => (
                <RetentionRow key={row.id} row={row} onSave={saveRetention} />
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="panel stack-gap">
        <h2 style={{ margin: 0 }}>{t("ops.flags")}</h2>
        <form className="row" onSubmit={upsertFlag}>
          <div className="field">
            <label>{t("ops.flagKey")}</label>
            <input
              value={flagKey}
              onChange={(e) => setFlagKey(e.target.value)}
              pattern="^[a-z0-9_.\-]+$"
              required
            />
          </div>
          <label className="field" style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
            <input
              type="checkbox"
              checked={flagOn}
              onChange={(e) => setFlagOn(e.target.checked)}
            />
            {t("ops.enabled")}
          </label>
          <button className="btn" type="submit">
            {t("ops.saveFlag")}
          </button>
        </form>
        {flags.length === 0 ? (
          <p className="muted">{t("ops.flagsEmpty")}</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>{t("ops.flagKey")}</th>
                <th>{t("ops.enabled")}</th>
              </tr>
            </thead>
            <tbody>
              {flags.map((f) => (
                <tr key={f.id}>
                  <td>
                    <code>{f.key}</code>
                  </td>
                  <td>
                    <span className={`badge ${f.enabled ? "ok" : "warn"}`}>
                      {f.enabled ? t("schedules.on") : t("schedules.off")}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="panel stack-gap">
        <h2 style={{ margin: 0 }}>{t("ops.members")}</h2>
        <form
          className="row"
          onSubmit={async (e) => {
            e.preventDefault();
            if (!projectId) return;
            try {
              const inv = await api.createInvite(projectId, {
                email: inviteEmail,
                role: "viewer",
              });
              setInviteToken(inv.token);
              setMsg(t("ops.invited"));
              setInviteEmail("");
              await reload(projectId);
            } catch (err) {
              setMsg(err instanceof Error ? err.message : t("ops.inviteFail"));
            }
          }}
        >
          <div className="field">
            <label>{t("ops.inviteEmail")}</label>
            <input
              type="email"
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
              required
            />
          </div>
          <button className="btn" type="submit">
            {t("ops.invite")}
          </button>
        </form>
        {inviteToken ? <pre className="log-box">{inviteToken}</pre> : null}
        {members.length === 0 ? (
          <p className="muted">{t("ops.membersEmpty")}</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>user_id</th>
                <th>{t("ops.role")}</th>
              </tr>
            </thead>
            <tbody>
              {members.map((m) => (
                <tr key={m.id}>
                  <td className="muted">{m.user_id}</td>
                  <td>{m.role}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}

function RetentionRow({
  row,
  onSave,
}: {
  row: { kind: string; keep_days: number; is_enabled: boolean };
  onSave: (kind: string, keepDays: number, enabled: boolean) => void;
}) {
  const { t } = useI18n();
  const [days, setDays] = useState(row.keep_days);
  const [enabled, setEnabled] = useState(row.is_enabled);

  useEffect(() => {
    setDays(row.keep_days);
    setEnabled(row.is_enabled);
  }, [row.keep_days, row.is_enabled]);

  return (
    <tr>
      <td>
        <code>{row.kind}</code>
      </td>
      <td>
        <input
          type="number"
          min={1}
          max={3650}
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          style={{ width: 96 }}
        />
      </td>
      <td>
        <input type="checkbox" checked={enabled} onChange={(e) => setEnabled(e.target.checked)} />
      </td>
      <td>
        <button className="btn ghost" type="button" onClick={() => onSave(row.kind, days, enabled)}>
          {t("ops.save")}
        </button>
      </td>
    </tr>
  );
}
