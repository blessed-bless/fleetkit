import { useEffect, useState } from "react";
import { api } from "../api";
import { EmptyState } from "../components/EmptyState";
import { useI18n } from "../i18n";

type ScenarioRow = { name: string; description: string };

export function ScenariosPage() {
  const { t } = useI18n();
  const [items, setItems] = useState<ScenarioRow[]>([]);
  const [active, setActive] = useState("");
  const [detail, setDetail] = useState<Record<string, unknown> | null>(null);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    api
      .scenarios()
      .then((rows) => {
        const list = rows as ScenarioRow[];
        setItems(list);
        if (list[0]) setActive(list[0].name);
      })
      .catch((e) => setMsg(e instanceof Error ? e.message : t("scenarios.fail")));
  }, [t]);

  useEffect(() => {
    if (!active) return;
    api
      .scenario(active)
      .then(setDetail)
      .catch((e) => setMsg(e instanceof Error ? e.message : t("scenarios.fail")));
  }, [active, t]);

  return (
    <div className="stack-gap">
      <div className="page-head">
        <div>
          <h1>{t("scenarios.title")}</h1>
          <p className="lead">{t("scenarios.lead")}</p>
        </div>
      </div>
      {msg ? <p className="error">{msg}</p> : null}
      <div className="split">
        <section className="panel">
          {items.length === 0 ? (
            <EmptyState title={t("scenarios.empty")} hint={t("scenarios.emptyHint")} />
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>{t("scenarios.name")}</th>
                  <th>{t("scenarios.description")}</th>
                </tr>
              </thead>
              <tbody>
                {items.map((row) => (
                  <tr
                    key={row.name}
                    className={active === row.name ? "selected" : ""}
                    style={{ cursor: "pointer" }}
                    onClick={() => setActive(row.name)}
                  >
                    <td>{row.name}</td>
                    <td className="muted">{row.description || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
        <aside className="panel stack-gap">
          <h2 style={{ margin: 0 }}>{t("scenarios.detail")}</h2>
          {detail ? (
            <pre className="log-box">{JSON.stringify(detail, null, 2)}</pre>
          ) : (
            <p className="muted">{t("scenarios.pick")}</p>
          )}
        </aside>
      </div>
    </div>
  );
}
