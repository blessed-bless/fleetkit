import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { useLiveProject } from "../hooks/useLive";
import { useI18n } from "../i18n";
import { useProject } from "../project";

export function OverviewPage() {
  const { t } = useI18n();
  const { projectId } = useProject();
  const [data, setData] = useState<Awaited<ReturnType<typeof api.overview>> | null>(null);
  const [error, setError] = useState("");
  const [tick, setTick] = useState(0);
  const live = useLiveProject(projectId || null, () => setTick((n) => n + 1));

  useEffect(() => {
    let alive = true;
    api
      .overview()
      .then((d) => {
        if (alive) setData(d);
      })
      .catch((err) => {
        if (alive) setError(err instanceof Error ? err.message : t("overview.unavailable"));
      });
    return () => {
      alive = false;
    };
  }, [tick, t]);

  useEffect(() => {
    const ms = live.connected ? 15000 : 5000;
    const id = window.setInterval(() => setTick((n) => n + 1), ms);
    return () => window.clearInterval(id);
  }, [live.connected]);

  if (error) return <p className="error">{error}</p>;
  if (!data) return <p className="muted">{t("overview.loading")}</p>;

  const attention =
    data.jobs_failed_24h > 0
      ? { className: "attention critical", text: t("overview.attnFail", { n: data.jobs_failed_24h }) }
      : data.jobs_queued > 0
        ? {
            className: "attention",
            text: t("overview.attnQueue", { n: data.jobs_queued, w: data.workers_online }),
          }
        : { className: "attention quiet", text: t("overview.attnOk") };

  return (
    <div className="stack-gap">
      <div className="page-head">
        <div>
          <h1>{t("overview.title")}</h1>
          <p className="lead">{t("overview.lead")}</p>
        </div>
        <span className="live-dot">
          <i /> {live.connected ? t("live.ws") : t("live.polling")}
        </span>
      </div>
      <div className={attention.className}>{attention.text}</div>
      {data.apps === 0 || data.workers_online === 0 ? (
        <section className="panel stack-gap onboard">
          <h2>{t("overview.startTitle")}</h2>
          <ol className="checklist">
            <li className={data.apps > 0 ? "done" : ""}>
              <Link to="/apps">{t("overview.startApp")}</Link>
            </li>
            <li className={data.apps > 0 ? "done" : ""}>
              <Link to="/settings">{t("overview.startKey")}</Link>
            </li>
            <li className={data.workers_online > 0 ? "done" : ""}>
              <span>{t("overview.startWorker")}</span>
            </li>
            <li>
              <Link to="/jobs">{t("overview.startJob")}</Link>
            </li>
            <li>
              <Link to="/webhooks">{t("overview.startWebhook")}</Link>
            </li>
          </ol>
        </section>
      ) : null}
      <div className="grid stats">
        <div className="stat">
          <div className="label">{t("overview.projects")}</div>
          <div className="value">{data.projects}</div>
        </div>
        <div className="stat">
          <div className="label">{t("overview.apps")}</div>
          <div className="value">{data.apps}</div>
        </div>
        <div className={`stat ${data.workers_online > 0 ? "attn-ok" : "attn-warn"}`}>
          <div className="label">{t("overview.workersOnline")}</div>
          <div className="value">{data.workers_online}</div>
        </div>
        <div className={`stat ${data.jobs_queued > 0 ? "attn-warn" : ""}`}>
          <div className="label">{t("overview.queued")}</div>
          <div className="value">{data.jobs_queued}</div>
        </div>
        <div className={`stat ${data.jobs_running > 0 ? "attn-run" : ""}`}>
          <div className="label">{t("overview.running")}</div>
          <div className="value">{data.jobs_running}</div>
        </div>
        <div className={`stat ${data.jobs_failed_24h > 0 ? "attn-err" : "attn-ok"}`}>
          <div className="label">{t("overview.failed24h")}</div>
          <div className="value">{data.jobs_failed_24h}</div>
        </div>
      </div>
      <section className="panel">
        <h2>{t("overview.events")}</h2>
        {data.recent_events.length === 0 ? (
          <p className="muted">{t("overview.eventsEmpty")}</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>{t("overview.when")}</th>
                <th>{t("overview.type")}</th>
                <th>{t("overview.message")}</th>
              </tr>
            </thead>
            <tbody>
              {data.recent_events.map((ev) => (
                <tr key={ev.id}>
                  <td className="muted">{new Date(ev.created_at).toLocaleString()}</td>
                  <td>
                    <span className={`badge ${ev.level === "error" ? "err" : ""}`}>{ev.kind}</span>
                  </td>
                  <td>{ev.message}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
