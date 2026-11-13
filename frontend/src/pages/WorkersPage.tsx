import { useEffect, useState } from "react";
import { api } from "../api";
import { EmptyState } from "../components/EmptyState";
import { useI18n } from "../i18n";
import { ProjectPicker, useProject } from "../project";

export function WorkersPage() {
  const { t } = useI18n();
  const { projectId } = useProject();
  const [workers, setWorkers] = useState<Awaited<ReturnType<typeof api.workers>>>([]);
  const [msg, setMsg] = useState("");

  async function reload() {
    if (!projectId) return;
    setWorkers(await api.workers(projectId));
  }

  useEffect(() => {
    if (!projectId) return;
    reload().catch(console.error);
    const id = window.setInterval(() => reload().catch(console.error), 5000);
    return () => window.clearInterval(id);
  }, [projectId]);

  async function toggleDrain(workerId: string, status: string) {
    if (!projectId) return;
    const draining = status !== "draining";
    try {
      await api.drainWorker(projectId, workerId, draining);
      setMsg(draining ? t("workers.drainOn") : t("workers.drainOff"));
      await reload();
    } catch (err) {
      setMsg(err instanceof Error ? err.message : t("workers.drainFail"));
    }
  }

  return (
    <div className="stack-gap">
      <div className="page-head">
        <div>
          <h1>{t("workers.title")}</h1>
          <p className="lead">{t("workers.lead")}</p>
        </div>
        <span className="live-dot">
          <i /> {t("live.ws")}
        </span>
      </div>
      <ProjectPicker />
      {msg ? <p className="muted">{msg}</p> : null}
      <section className="panel">
        {workers.length === 0 ? (
          <EmptyState title={t("workers.empty")} hint={t("workers.lead")} />
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>{t("workers.name")}</th>
                <th>{t("workers.host")}</th>
                <th>{t("workers.status")}</th>
                <th>{t("workers.heartbeat")}</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {workers.map((w) => (
                <tr key={w.id}>
                  <td>{w.name}</td>
                  <td>{w.hostname || "—"}</td>
                  <td>
                    <span
                      className={`badge ${
                        w.status === "online" ? "ok" : w.status === "draining" ? "warn" : "warn"
                      }`}
                    >
                      {w.status}
                    </span>
                  </td>
                  <td className="muted">
                    {w.last_heartbeat_at
                      ? new Date(w.last_heartbeat_at).toLocaleString()
                      : t("workers.never")}
                  </td>
                  <td>
                    <button
                      className="btn ghost"
                      type="button"
                      onClick={() => toggleDrain(w.id, w.status)}
                    >
                      {w.status === "draining" ? t("workers.resume") : t("workers.drain")}
                    </button>
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
