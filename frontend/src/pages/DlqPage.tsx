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
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState<string | null>(null);

  async function reload(id: string) {
    setItems(await api.deadLetters(id));
    setSelected(new Set());
  }

  useEffect(() => {
    if (projectId) reload(projectId).catch((e) => setMsg(e.message));
  }, [projectId]);

  async function requeue(id: string) {
    if (!projectId) return;
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

  async function discard(id: string) {
    if (!projectId) return;
    setBusy(id);
    try {
      await api.discardDeadLetter(projectId, id);
      setMsg(t("dlq.discarded"));
      await reload(projectId);
    } catch (err) {
      setMsg(err instanceof Error ? err.message : t("dlq.discardFail"));
    } finally {
      setBusy(null);
    }
  }

  async function requeueSelected() {
    if (!projectId || selected.size === 0) return;
    setBusy("bulk");
    try {
      const res = await api.requeueDeadLettersBulk(projectId, [...selected]);
      setMsg(t("dlq.bulkRequeued", { n: res.count }));
      await reload(projectId);
    } catch (err) {
      setMsg(err instanceof Error ? err.message : t("dlq.requeueFail"));
    } finally {
      setBusy(null);
    }
  }

  function toggle(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  return (
    <div className="stack-gap">
      <div className="page-head">
        <div>
          <h1>{t("dlq.title")}</h1>
          <p className="lead">{t("dlq.lead")}</p>
        </div>
        <button
          className="btn"
          type="button"
          disabled={selected.size === 0 || busy === "bulk"}
          onClick={() => requeueSelected()}
        >
          {t("dlq.requeueSelected", { n: selected.size })}
        </button>
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
                <th />
                <th>{t("dlq.job")}</th>
                <th>{t("dlq.error")}</th>
                <th>{t("dlq.attempts")}</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id}>
                  <td>
                    <input
                      className="check"
                      type="checkbox"
                      checked={selected.has(item.id)}
                      disabled={item.requeued}
                      onChange={() => toggle(item.id)}
                    />
                  </td>
                  <td>{item.job_name}</td>
                  <td>{item.error}</td>
                  <td>{item.attempts}</td>
                  <td className="row" style={{ gap: 6 }}>
                    <button
                      className="btn"
                      type="button"
                      disabled={busy === item.id || item.requeued}
                      onClick={() => requeue(item.id)}
                    >
                      {busy === item.id ? t("dlq.requeuing") : t("dlq.requeue")}
                    </button>
                    <button
                      className="btn ghost"
                      type="button"
                      disabled={busy === item.id || item.requeued}
                      onClick={() => discard(item.id)}
                    >
                      {t("dlq.discard")}
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
