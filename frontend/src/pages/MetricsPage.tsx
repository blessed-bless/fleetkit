import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import { useI18n } from "../i18n";
import { ProjectPicker, useProject } from "../project";

export function MetricsPage() {
  const { t } = useI18n();
  const { projectId } = useProject();
  const [values, setValues] = useState<Record<string, number>>({});
  const [outcomes, setOutcomes] = useState<Record<string, number>>({});
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);

  const max = useMemo(() => Math.max(1, ...Object.values(values)), [values]);
  const outcomeMax = useMemo(() => Math.max(1, ...Object.values(outcomes)), [outcomes]);

  async function snapshot() {
    if (!projectId) return;
    setBusy(true);
    try {
      const [snap, out] = await Promise.all([
        api.snapshotMetrics(projectId),
        api.metricOutcomes(projectId, 24),
      ]);
      setValues(snap);
      setOutcomes(out);
      setMsg(t("metrics.done"));
    } catch (err) {
      setMsg(err instanceof Error ? err.message : t("metrics.fail"));
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    if (projectId) snapshot();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  return (
    <div className="stack-gap">
      <div className="page-head">
        <div>
          <h1>{t("metrics.title")}</h1>
          <p className="lead">{t("metrics.lead")}</p>
        </div>
        <button className="btn" type="button" onClick={snapshot} disabled={busy || !projectId}>
          {busy ? t("metrics.busy") : t("metrics.snapshot")}
        </button>
      </div>
      <ProjectPicker />
      {msg ? <p className="muted">{msg}</p> : null}
      {Object.keys(values).length === 0 ? (
        <p className="muted">{t("metrics.empty")}</p>
      ) : (
        <div className="grid stats">
          {Object.entries(values).map(([key, value]) => (
            <div className="stat" key={key}>
              <div className="label">{key}</div>
              <div className="value">{value}</div>
              <div className="metric-bar">
                <span style={{ width: `${Math.max(4, (value / max) * 100)}%` }} />
              </div>
            </div>
          ))}
        </div>
      )}
      {Object.keys(outcomes).length > 0 ? (
        <section className="panel stack-gap">
          <h2 style={{ margin: 0 }}>{t("metrics.outcomes")}</h2>
          <div className="grid stats">
            {Object.entries(outcomes).map(([key, value]) => (
              <div className="stat" key={key}>
                <div className="label">{key}</div>
                <div className="value">{value}</div>
                <div className="metric-bar">
                  <span style={{ width: `${Math.max(4, (value / outcomeMax) * 100)}%` }} />
                </div>
              </div>
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}
