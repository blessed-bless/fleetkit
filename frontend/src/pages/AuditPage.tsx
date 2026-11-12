import { useEffect, useState } from "react";
import { api } from "../api";
import { EmptyState } from "../components/EmptyState";
import { useI18n } from "../i18n";
import { ProjectPicker, useProject } from "../project";

export function AuditPage() {
  const { t } = useI18n();
  const { projectId } = useProject();
  const [items, setItems] = useState<Awaited<ReturnType<typeof api.audit>>>([]);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    if (!projectId) return;
    api
      .audit(projectId)
      .then(setItems)
      .catch((e) => setMsg(e instanceof Error ? e.message : t("audit.fail")));
  }, [projectId, t]);

  return (
    <div className="stack-gap">
      <div className="page-head">
        <div>
          <h1>{t("audit.title")}</h1>
          <p className="lead">{t("audit.lead")}</p>
        </div>
      </div>
      <ProjectPicker />
      {msg ? <p className="error">{msg}</p> : null}
      <section className="panel">
        {items.length === 0 ? (
          <EmptyState title={t("audit.empty")} hint={t("audit.emptyHint")} />
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>{t("audit.when")}</th>
                <th>{t("audit.action")}</th>
                <th>{t("audit.resource")}</th>
              </tr>
            </thead>
            <tbody>
              {items.map((row) => (
                <tr key={row.id}>
                  <td className="muted">{new Date(row.created_at).toLocaleString()}</td>
                  <td>
                    <code>{row.action}</code>
                  </td>
                  <td>
                    {row.resource_type}{" "}
                    <span className="muted">{row.resource_id}</span>
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
