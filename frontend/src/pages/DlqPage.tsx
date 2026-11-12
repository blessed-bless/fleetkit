import { useEffect, useState } from "react";
import { api } from "../api";
import { EmptyState } from "../components/EmptyState";
import { useI18n } from "../i18n";
import { ProjectPicker, useProject } from "../project";

export function DlqPage() {
  const { t } = useI18n();
  const { projectId } = useProject();
  const [items, setItems] = useState<
    Array<{ id: string; job_name: string; error: string; attempts: number; requeued: boolean }>
  >([]);
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState<string | null>(null);

  async function reload(id: string) {
    setItems(await api.deadLetters(id));
  }

  useEffect(() => {
    if (projectId) reload(projectId).catch((e) => setMsg(e.message));
  }, [projectId]);

  async function requeue(id: string) {
    setBusy(id);
    try {
      const res = await api.requeueDeadLetter(projectId, id);
      setMsg(t("dlq.requeued", { id: res.job_id }));
      await reload(projectId);
    } catch (err) {
      setMsg(err instanceof Error ? err.message : t("dlq.requeueFail"));
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="stack-gap">
      <div className="page-head">
        <div>
          <h1>{t("dlq.title")}</h1>
          <p className="lead">{t("dlq.lead")}</p>
        </div>
      </div>
      <ProjectPicker />
      {msg ? <p className="muted">{msg}</p> : null}
      <section className="panel">
        {items.length === 0 ? (
          <EmptyState title={t("dlq.empty")} hint={t("dlq.lead")} />
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>{t("dlq.job")}</th>
                <th>{t("dlq.error")}</th>
                <th>{t("dlq.attempts")}</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id}>
                  <td>{item.job_name}</td>
                  <td>{item.error}</td>
                  <td>{item.attempts}</td>
                  <td>
                    <button
                      className="btn"
                      type="button"
                      disabled={busy === item.id || item.requeued}
                      onClick={() => requeue(item.id)}
                    >
                      {busy === item.id ? t("dlq.requeuing") : t("dlq.requeue")}
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
