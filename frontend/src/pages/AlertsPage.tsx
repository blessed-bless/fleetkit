import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { api } from "../api";
import { EmptyState } from "../components/EmptyState";
import { useI18n } from "../i18n";
import { ProjectPicker, useProject } from "../project";

export function AlertsPage() {
  const { t } = useI18n();
  const { projectId } = useProject();
  const [rules, setRules] = useState<Awaited<ReturnType<typeof api.alertRules>>>([]);
  const [fires, setFires] = useState<Awaited<ReturnType<typeof api.alertFires>>>([]);
  const [channels, setChannels] = useState<Awaited<ReturnType<typeof api.channels>>>([]);
  const [name, setName] = useState("Queue too deep");
  const [expression, setExpression] = useState("queue.depth>20");
  const [channelName, setChannelName] = useState("ops-webhook");
  const [channelKind, setChannelKind] = useState("webhook");
  const [channelTarget, setChannelTarget] = useState("https://example.com/hooks/fleetkit");
  const [msg, setMsg] = useState("");

  async function reload(id: string) {
    const [r, f, c] = await Promise.all([
      api.alertRules(id),
      api.alertFires(id),
      api.channels(id),
    ]);
    setRules(r);
    setFires(f);
    setChannels(c);
  }

  useEffect(() => {
    if (projectId) reload(projectId).catch((e) => setMsg(e.message));
  }, [projectId]);

  async function create(e: FormEvent) {
    e.preventDefault();
    await api.createAlertRule(projectId, { name, expression, severity: "warning" });
    setMsg(t("alerts.added"));
    await reload(projectId);
  }

  async function createChannel(e: FormEvent) {
    e.preventDefault();
    const config =
      channelKind === "telegram"
        ? (() => {
            const [botToken, chatId] = channelTarget.split("|", 2);
            return chatId
              ? { bot_token: botToken.trim(), chat_id: chatId.trim() }
              : { chat_id: channelTarget.trim() };
          })()
        : channelKind === "email"
          ? { to: channelTarget.trim() }
          : {
              url: channelTarget.trim(),
              ...(channelTarget.includes("hooks.slack.com") ? { format: "slack" } : {}),
            };
    await api.createChannel(projectId, { name: channelName, kind: channelKind, config });
    setMsg(t("alerts.channelAdded"));
    await reload(projectId);
  }

  async function evaluate() {
    const res = await api.evaluateAlerts(projectId);
    setMsg(t("alerts.fired", { n: res.fired }));
    await reload(projectId);
  }

  return (
    <div className="stack-gap">
      <div className="page-head">
        <div>
          <h1>{t("alerts.title")}</h1>
          <p className="lead">{t("alerts.lead")}</p>
        </div>
      </div>
      <ProjectPicker />
      <form className="panel row" onSubmit={create}>
        <div className="field">
          <label>{t("alerts.name")}</label>
          <input value={name} onChange={(e) => setName(e.target.value)} required />
        </div>
        <div className="field">
          <label>{t("alerts.expr")}</label>
          <input value={expression} onChange={(e) => setExpression(e.target.value)} required />
        </div>
        <button className="btn" type="submit">
          {t("alerts.add")}
        </button>
        <button className="btn ghost" type="button" onClick={evaluate}>
          {t("alerts.checkNow")}
        </button>
      </form>
      {msg ? <p className="muted">{msg}</p> : null}

      <section className="panel stack-gap">
        <h2 style={{ margin: 0 }}>{t("alerts.channels")}</h2>
        <form className="row" onSubmit={createChannel}>
          <div className="field">
            <label>{t("alerts.channelName")}</label>
            <input value={channelName} onChange={(e) => setChannelName(e.target.value)} required />
          </div>
          <div className="field">
            <label>{t("alerts.channelKind")}</label>
            <select value={channelKind} onChange={(e) => setChannelKind(e.target.value)}>
              <option value="webhook">webhook</option>
              <option value="telegram">telegram</option>
              <option value="email">email</option>
            </select>
          </div>
          <div className="field" style={{ minWidth: 260 }}>
            <label>{t("alerts.channelTarget")}</label>
            <input
              value={channelTarget}
              onChange={(e) => setChannelTarget(e.target.value)}
              required
            />
          </div>
          <button className="btn" type="submit">
            {t("alerts.addChannel")}
          </button>
        </form>
        {channels.length === 0 ? (
          <EmptyState title={t("alerts.channelsEmpty")} hint={t("alerts.channelsHint")} />
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>{t("alerts.channelName")}</th>
                <th>{t("alerts.channelKind")}</th>
                <th>{t("apps.status")}</th>
              </tr>
            </thead>
            <tbody>
              {channels.map((c) => (
                <tr key={c.id}>
                  <td>{c.name}</td>
                  <td>{c.kind}</td>
                  <td>
                    <span className={`badge ${c.is_enabled ? "ok" : "warn"}`}>
                      {c.is_enabled ? t("schedules.on") : t("schedules.off")}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="panel">
        <h2>{t("alerts.rules")}</h2>
        <table className="table">
          <thead>
            <tr>
              <th>{t("alerts.name")}</th>
              <th>{t("alerts.expr")}</th>
              <th>{t("alerts.severity")}</th>
            </tr>
          </thead>
          <tbody>
            {rules.map((r) => (
              <tr key={r.id}>
                <td>{r.name}</td>
                <td>{r.expression}</td>
                <td>{r.severity}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      <section className="panel">
        <h2>{t("alerts.fires")}</h2>
        {fires.length === 0 ? (
          <p className="muted">{t("alerts.firesEmpty")}</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>{t("alerts.when")}</th>
                <th>{t("alerts.message")}</th>
              </tr>
            </thead>
            <tbody>
              {fires.map((f) => (
                <tr key={f.id}>
                  <td className="muted">{new Date(f.created_at).toLocaleString()}</td>
                  <td>{f.message}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
