import { useCallback, useEffect, useState } from "react";
import type { FormEvent, ReactNode } from "react";
import { Link, Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { ApiError, api, tokenStore } from "./api";
import { EmptyState } from "./components/EmptyState";
import { useLiveProject } from "./hooks/useLive";
import { LangSwitch, useI18n } from "./i18n";
import { AlertsPage } from "./pages/AlertsPage";
import { DlqPage } from "./pages/DlqPage";
import { SearchPage } from "./pages/SearchPage";
import { MetricsPage } from "./pages/MetricsPage";
import { SecretsPage } from "./pages/SecretsPage";
import { SchedulesPage } from "./pages/SchedulesPage";
import { AuditPage } from "./pages/AuditPage";
import { HealthPage } from "./pages/HealthPage";
import { OpsPage } from "./pages/OpsPage";
import { ScenariosPage } from "./pages/ScenariosPage";
import { TemplatesPage } from "./pages/TemplatesPage";
import { WebhooksPage } from "./pages/WebhooksPage";
import { ProjectPicker, ProjectProvider, useProject } from "./project";

type JobRow = Awaited<ReturnType<typeof api.jobs>>[number];

function useAuth() {
  const [ready, setReady] = useState(false);
  const [email, setEmail] = useState<string | null>(null);

  useEffect(() => {
    const token = tokenStore.get();
    if (!token) {
      setReady(true);
      return;
    }
    api
      .me()
      .then((u) => setEmail(u.email))
      .catch(() => tokenStore.set(null))
      .finally(() => setReady(true));
  }, []);

  return { ready, email, setEmail, loggedIn: Boolean(email) };
}

function Shell({
  email,
  onLogout,
  children,
}: {
  email: string;
  onLogout: () => void;
  children: ReactNode;
}) {
  const loc = useLocation();
  const { t } = useI18n();
  const groups: Array<{ label: string; items: Array<[string, string]> }> = [
    { label: t("nav.groupMain"), items: [["/", t("nav.overview")]] },
    {
      label: t("nav.groupWork"),
      items: [
        ["/apps", t("nav.apps")],
        ["/jobs", t("nav.jobs")],
        ["/workers", t("nav.workers")],
        ["/schedules", t("nav.schedules")],
        ["/webhooks", t("nav.webhooks")],
        ["/templates", t("nav.templates")],
        ["/scenarios", t("nav.scenarios")],
      ],
    },
    {
      label: t("nav.groupObserve"),
      items: [
        ["/health", t("nav.health")],
        ["/alerts", t("nav.alerts")],
        ["/dlq", t("nav.dlq")],
        ["/search", t("nav.search")],
        ["/metrics", t("nav.metrics")],
      ],
    },
    {
      label: t("nav.groupAdmin"),
      items: [
        ["/secrets", t("nav.secrets")],
        ["/ops", t("nav.ops")],
        ["/audit", t("nav.audit")],
        ["/settings", t("nav.settings")],
      ],
    },
  ];

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          Fleet<span>Kit</span>
        </div>
        <nav className="side-nav">
          {groups.map((g) => (
            <div key={g.label} className="nav-group">
              <div className="nav-group-label">{g.label}</div>
              {g.items.map(([to, label]) => (
                <Link key={to} to={to} className={loc.pathname === to ? "active" : ""}>
                  {label}
                </Link>
              ))}
            </div>
          ))}
        </nav>
        <div className="side-foot">
          <LangSwitch />
          <span className="muted" style={{ fontSize: "0.85rem", padding: "0 8px" }}>
            {email}
          </span>
          <button className="btn ghost" type="button" onClick={onLogout}>
            {t("nav.logout")}
          </button>
        </div>
      </aside>
      <main className="main" key={loc.pathname}>
        {children}
      </main>
    </div>
  );
}

function LoginPage({ onLogin }: { onLogin: (email: string) => void }) {
  const { t } = useI18n();
  const [email, setEmail] = useState("admin@example.com");
  const [password, setPassword] = useState("fleetkit-admin");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const tok = await api.login(email, password);
      tokenStore.set(tok.access_token);
      onLogin(email);
    } catch (err) {
      if (err instanceof ApiError) setError(err.message);
      else setError(t("login.apiDown"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-wrap">
      <form className="panel login-card stack-gap" onSubmit={submit}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
          <div>
            <div className="brand">
              Fleet<span>Kit</span>
            </div>
            <h1>{t("login.title")}</h1>
            <p className="muted">{t("login.lead")}</p>
          </div>
          <LangSwitch />
        </div>
        <div className="field">
          <label htmlFor="email">{t("login.email")}</label>
          <input id="email" value={email} onChange={(e) => setEmail(e.target.value)} />
        </div>
        <div className="field">
          <label htmlFor="password">{t("login.password")}</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        {error ? <p className="error">{error}</p> : null}
        <button className="btn" disabled={busy} type="submit">
          {busy ? t("login.checking") : t("login.submit")}
        </button>
      </form>
    </div>
  );
}

function statusBadge(status: string) {
  if (status === "succeeded") return "ok";
  if (status === "failed" || status === "timed_out") return "err";
  if (status === "running") return "run";
  if (status === "queued" || status === "cancelled") return "warn";
  return "";
}

function OverviewPage() {
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

function AppsPage() {
  const { t } = useI18n();
  const { projectId, error } = useProject();
  const [apps, setApps] = useState<Awaited<ReturnType<typeof api.apps>>>([]);
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [kind, setKind] = useState("worker");
  const [msg, setMsg] = useState("");
  const [selectedApp, setSelectedApp] = useState("");
  const [envRows, setEnvRows] = useState<Awaited<ReturnType<typeof api.appEnv>>>([]);
  const [envKey, setEnvKey] = useState("LOG_LEVEL");
  const [envValue, setEnvValue] = useState("info");
  const [envSecret, setEnvSecret] = useState(false);

  async function reload(id: string) {
    const list = await api.apps(id);
    setApps(list);
    if (list[0] && !selectedApp) setSelectedApp(list[0].id);
  }

  async function reloadEnv(appId: string) {
    if (!projectId || !appId) return;
    setEnvRows(await api.appEnv(projectId, appId));
  }

  useEffect(() => {
    if (projectId) reload(projectId).catch((err) => setMsg(err.message));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  useEffect(() => {
    if (selectedApp) reloadEnv(selectedApp).catch((err) => setMsg(err.message));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedApp, projectId]);

  async function create(e: FormEvent) {
    e.preventDefault();
    if (!projectId) return;
    setMsg("");
    try {
      await api.createApp(projectId, { name, slug, kind });
      setName("");
      setSlug("");
      await reload(projectId);
      setMsg(t("apps.created"));
    } catch (err) {
      setMsg(err instanceof Error ? err.message : t("apps.createFail"));
    }
  }

  async function toggle(appId: string, enabled: boolean) {
    if (!projectId) return;
    try {
      await api.patchApp(projectId, appId, { is_enabled: !enabled });
      await reload(projectId);
      setMsg(!enabled ? t("apps.enabledMsg") : t("apps.disabledMsg"));
    } catch (err) {
      setMsg(err instanceof Error ? err.message : t("apps.toggleFail"));
    }
  }

  return (
    <div className="stack-gap">
      <div className="page-head">
        <div>
          <h1>{t("apps.title")}</h1>
          <p className="lead">{t("apps.lead")}</p>
        </div>
      </div>
      {error ? <p className="error">{error}</p> : null}
      <ProjectPicker />
      <form className="panel row" onSubmit={create}>
        <div className="field">
          <label>{t("apps.name")}</label>
          <input value={name} onChange={(e) => setName(e.target.value)} required />
        </div>
        <div className="field">
          <label>{t("apps.slug")}</label>
          <input
            value={slug}
            onChange={(e) => setSlug(e.target.value)}
            pattern="^[a-z0-9][a-z0-9\-]*$"
            required
          />
        </div>
        <div className="field">
          <label>{t("apps.kind")}</label>
          <select value={kind} onChange={(e) => setKind(e.target.value)}>
            <option value="worker">worker</option>
            <option value="bot">bot</option>
            <option value="cron">cron</option>
            <option value="webhook">webhook</option>
          </select>
        </div>
        <button className="btn" type="submit">
          {t("apps.create")}
        </button>
      </form>
      {msg ? <p className="muted">{msg}</p> : null}
      <section className="panel">
        {apps.length === 0 ? (
          <EmptyState title={t("apps.empty")} hint={t("apps.emptyHint")} />
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>{t("apps.name")}</th>
                <th>{t("apps.slug")}</th>
                <th>{t("apps.kind")}</th>
                <th>{t("apps.status")}</th>
                <th />
                <th>ID</th>
              </tr>
            </thead>
            <tbody>
              {apps.map((app) => (
                <tr
                  key={app.id}
                  className={selectedApp === app.id ? "selected" : ""}
                  onClick={() => setSelectedApp(app.id)}
                  style={{ cursor: "pointer" }}
                >
                  <td>{app.name}</td>
                  <td>{app.slug}</td>
                  <td>{app.kind}</td>
                  <td>
                    <span className={`badge ${app.is_enabled ? "ok" : "warn"}`}>
                      {app.is_enabled ? t("apps.enabled") : t("apps.disabled")}
                    </span>
                  </td>
                  <td>
                    <button
                      className="btn ghost"
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        toggle(app.id, app.is_enabled);
                      }}
                    >
                      {app.is_enabled ? t("apps.disable") : t("apps.enable")}
                    </button>
                  </td>
                  <td className="muted">{app.id}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
      {selectedApp ? (
        <section className="panel stack-gap">
          <h2 style={{ margin: 0 }}>{t("apps.envTitle")}</h2>
          <form
            className="row"
            onSubmit={async (e) => {
              e.preventDefault();
              if (!projectId || !selectedApp) return;
              try {
                await api.upsertAppEnv(projectId, selectedApp, {
                  key: envKey,
                  value: envValue,
                  is_secret: envSecret,
                });
                setMsg(t("apps.envSaved"));
                setEnvValue("");
                await reloadEnv(selectedApp);
              } catch (err) {
                setMsg(err instanceof Error ? err.message : t("apps.envFail"));
              }
            }}
          >
            <div className="field">
              <label>{t("apps.envKey")}</label>
              <input
                value={envKey}
                onChange={(e) => setEnvKey(e.target.value)}
                pattern="^[A-Z][A-Z0-9_]*$"
                required
              />
            </div>
            <div className="field">
              <label>{t("apps.envValue")}</label>
              <input value={envValue} onChange={(e) => setEnvValue(e.target.value)} required />
            </div>
            <label className="field" style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
              <input
                type="checkbox"
                checked={envSecret}
                onChange={(e) => setEnvSecret(e.target.checked)}
              />
              {t("apps.envSecret")}
            </label>
            <button className="btn" type="submit">
              {t("apps.envSave")}
            </button>
          </form>
          {envRows.length === 0 ? (
            <p className="muted">{t("apps.envEmpty")}</p>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>{t("apps.envKey")}</th>
                  <th>{t("apps.envValue")}</th>
                </tr>
              </thead>
              <tbody>
                {envRows.map((row) => (
                  <tr key={row.id}>
                    <td>
                      <code>{row.key}</code>
                    </td>
                    <td className="muted">{row.value_preview}</td>
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

function JobsPage() {
  const { t } = useI18n();
  const { projectId } = useProject();
  const [apps, setApps] = useState<Awaited<ReturnType<typeof api.apps>>>([]);
  const [jobs, setJobs] = useState<JobRow[]>([]);
  const [appId, setAppId] = useState("");
  const [filterApp, setFilterApp] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [filterQ, setFilterQ] = useState("");
  const [jobName, setJobName] = useState("ping");
  const [batchCount, setBatchCount] = useState(1);
  const [msg, setMsg] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [activeId, setActiveId] = useState<string | null>(null);
  const [detail, setDetail] = useState<JobRow | null>(null);
  const [logs, setLogs] = useState<Array<{ seq: number; stream: string; line: string }>>([]);
  const [liveOn, setLiveOn] = useState(true);

  const reload = useCallback(async () => {
    if (!projectId) return;
    const list = await api.jobs(projectId, {
      app_id: filterApp || undefined,
      status: filterStatus || undefined,
      q: filterQ || undefined,
      limit: 100,
    });
    setJobs(list);
  }, [projectId, filterApp, filterStatus, filterQ]);

  const live = useLiveProject(liveOn ? projectId || null : null, () => {
    reload().catch(() => undefined);
  });

  useEffect(() => {
    if (!projectId) return;
    api
      .apps(projectId)
      .then((a) => {
        setApps(a);
        if (a[0] && !appId) setAppId(a[0].id);
      })
      .catch((err) => setMsg(err.message));
  }, [projectId, appId]);

  useEffect(() => {
    reload().catch((err) => setMsg(err.message));
  }, [reload]);

  useEffect(() => {
    if (!liveOn) return;
    const ms = live.connected ? 20000 : 4000;
    const id = window.setInterval(() => {
      reload().catch(() => undefined);
    }, ms);
    return () => window.clearInterval(id);
  }, [liveOn, live.connected, reload]);

  useEffect(() => {
    if (!projectId || !activeId) {
      setDetail(null);
      setLogs([]);
      return;
    }
    let alive = true;
    Promise.all([api.job(projectId, activeId), api.jobLogs(projectId, activeId)])
      .then(([j, l]) => {
        if (!alive) return;
        setDetail(j);
        setLogs(l.map((x) => ({ seq: x.seq, stream: x.stream, line: x.line })));
      })
      .catch(() => undefined);
    return () => {
      alive = false;
    };
  }, [projectId, activeId, jobs]);

  async function enqueue(e: FormEvent) {
    e.preventDefault();
    if (!projectId || !appId) return;
    try {
      const n = Math.max(1, Math.min(100, Number(batchCount) || 1));
      if (n === 1) {
        await api.createJob(projectId, appId, { name: jobName, payload: { source: "dashboard" } });
        setMsg(t("jobs.queuedMsg"));
      } else {
        const res = await api.batchJobs(projectId, {
          app_id: appId,
          name: jobName,
          payloads: Array.from({ length: n }, (_, i) => ({ source: "dashboard", i })),
        });
        setMsg(t("jobs.batchQueued", { n: res.count }));
      }
      await reload();
    } catch (err) {
      setMsg(err instanceof Error ? err.message : t("jobs.enqueueFail"));
    }
  }

  async function cancelOne(id: string) {
    if (!projectId) return;
    await api.cancelJob(projectId, id);
    await reload();
    setMsg(t("jobs.cancelled"));
  }

  async function cancelSelected() {
    if (!projectId || selected.size === 0) return;
    const n = selected.size;
    await api.cancelJobsBulk(projectId, [...selected]);
    setSelected(new Set());
    await reload();
    setMsg(t("jobs.bulkCancelled", { n }));
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
          <h1>{t("jobs.title")}</h1>
          <p className="lead">{t("jobs.lead")}</p>
        </div>
        <button className="btn ghost" type="button" onClick={() => setLiveOn((v) => !v)}>
          {liveOn ? (
            <span className="live-dot">
              <i /> {live.connected ? t("live.ws") : t("live.polling")}
            </span>
          ) : (
            t("live.enable")
          )}
        </button>
      </div>
      <ProjectPicker />

      <form className="panel row" onSubmit={enqueue}>
        <div className="field">
          <label>{t("jobs.app")}</label>
          <select value={appId} onChange={(e) => setAppId(e.target.value)}>
            {apps.map((a) => (
              <option key={a.id} value={a.id}>
                {a.name}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label>{t("jobs.name")}</label>
          <input value={jobName} onChange={(e) => setJobName(e.target.value)} required />
        </div>
        <div className="field">
          <label>{t("jobs.batch")}</label>
          <input
            type="number"
            min={1}
            max={100}
            value={batchCount}
            onChange={(e) => setBatchCount(Number(e.target.value))}
          />
        </div>
        <button className="btn" type="submit" disabled={!appId}>
          {t("jobs.enqueue")}
        </button>
      </form>

      <div className="panel toolbar">
        <div className="field">
          <label>{t("jobs.status")}</label>
          <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
            <option value="">{t("jobs.statusAll")}</option>
            <option value="queued">queued</option>
            <option value="running">running</option>
            <option value="succeeded">succeeded</option>
            <option value="failed">failed</option>
            <option value="cancelled">cancelled</option>
          </select>
        </div>
        <div className="field">
          <label>{t("jobs.app")}</label>
          <select value={filterApp} onChange={(e) => setFilterApp(e.target.value)}>
            <option value="">{t("jobs.appAll")}</option>
            {apps.map((a) => (
              <option key={a.id} value={a.id}>
                {a.name}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label>{t("jobs.search")}</label>
          <input
            value={filterQ}
            onChange={(e) => setFilterQ(e.target.value)}
            placeholder="ping, sync..."
          />
        </div>
        <button
          className="btn danger"
          type="button"
          disabled={selected.size === 0}
          onClick={() => cancelSelected().catch((err) => setMsg(err.message))}
        >
          {t("jobs.cancelSelected", { n: selected.size })}
        </button>
      </div>

      {msg ? <p className="muted">{msg}</p> : null}

      <div className="split">
        <section className="panel">
          <table className="table">
            <thead>
              <tr>
                <th />
                <th>{t("jobs.name")}</th>
                <th>{t("jobs.status")}</th>
                <th>{t("jobs.queue")}</th>
                <th>{t("jobs.attempt")}</th>
                <th>{t("jobs.created")}</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {jobs.map((job) => (
                <tr
                  key={job.id}
                  className={activeId === job.id ? "selected" : ""}
                  onClick={() => setActiveId(job.id)}
                >
                  <td onClick={(e) => e.stopPropagation()}>
                    <input
                      className="check"
                      type="checkbox"
                      checked={selected.has(job.id)}
                      onChange={() => toggle(job.id)}
                    />
                  </td>
                  <td>{job.name}</td>
                  <td>
                    <span className={`badge ${statusBadge(job.status)}`}>{job.status}</span>
                  </td>
                  <td>{job.queue}</td>
                  <td>
                    {job.attempt}/{job.max_attempts}
                  </td>
                  <td className="muted">{new Date(job.created_at).toLocaleString()}</td>
                  <td onClick={(e) => e.stopPropagation()}>
                    {job.status === "queued" || job.status === "running" ? (
                      <button
                        className="btn ghost"
                        type="button"
                        onClick={() => cancelOne(job.id).catch((err) => setMsg(err.message))}
                      >
                        {t("jobs.cancel")}
                      </button>
                    ) : null}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {jobs.length === 0 ? <p className="muted">{t("jobs.empty")}</p> : null}
        </section>

        <aside className="panel drawer stack-gap">
          <h2>{t("jobs.details")}</h2>
          {!detail ? (
            <p className="muted">{t("jobs.detailsHint")}</p>
          ) : (
            <>
              <div>
                <strong>{detail.name}</strong>{" "}
                <span className={`badge ${statusBadge(detail.status)}`}>{detail.status}</span>
              </div>
              <p className="muted" style={{ margin: 0, fontSize: "0.85rem" }}>
                {detail.id}
              </p>
              {detail.error ? <p className="error">{detail.error}</p> : null}
              <div className="field">
                <label>{t("jobs.payload")}</label>
                <pre className="log-box">{JSON.stringify(detail.payload, null, 2)}</pre>
              </div>
              {detail.result ? (
                <div className="field">
                  <label>{t("jobs.result")}</label>
                  <pre className="log-box">{JSON.stringify(detail.result, null, 2)}</pre>
                </div>
              ) : null}
              <div className="field">
                <label>{t("jobs.logs")}</label>
                <div className="log-box">
                  {logs.length === 0 ? (
                    <span className="muted">{t("jobs.logsEmpty")}</span>
                  ) : (
                    logs.map((l) => (
                      <div key={l.seq} className={l.stream === "stderr" ? "stderr" : ""}>
                        [{l.seq}] {l.line}
                      </div>
                    ))
                  )}
                </div>
              </div>
            </>
          )}
        </aside>
      </div>
    </div>
  );
}

function WorkersPage() {
  const { t } = useI18n();
  const { projectId } = useProject();
  const [workers, setWorkers] = useState<Awaited<ReturnType<typeof api.workers>>>([]);

  useEffect(() => {
    if (!projectId) return;
    const load = () => api.workers(projectId).then(setWorkers).catch(console.error);
    load();
    const id = window.setInterval(load, 5000);
    return () => window.clearInterval(id);
  }, [projectId]);

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
              </tr>
            </thead>
            <tbody>
              {workers.map((w) => (
                <tr key={w.id}>
                  <td>{w.name}</td>
                  <td>{w.hostname || "—"}</td>
                  <td>
                    <span className={`badge ${w.status === "online" ? "ok" : "warn"}`}>
                      {w.status}
                    </span>
                  </td>
                  <td className="muted">
                    {w.last_heartbeat_at
                      ? new Date(w.last_heartbeat_at).toLocaleString()
                      : t("workers.never")}
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

function SettingsPage() {
  const { t } = useI18n();
  const { projectId, reload } = useProject();
  const [secret, setSecret] = useState("");
  const [keys, setKeys] = useState<Awaited<ReturnType<typeof api.apiKeys>>>([]);
  const [projName, setProjName] = useState("");
  const [projSlug, setProjSlug] = useState("");
  const [msg, setMsg] = useState("");

  useEffect(() => {
    if (!projectId) return;
    api.apiKeys(projectId).then(setKeys).catch((e) => setMsg(e.message));
  }, [projectId, secret]);

  async function mint() {
    if (!projectId) return;
    try {
      const key = await api.createApiKey(projectId, `key-${Date.now()}`);
      setSecret(key.secret);
      setMsg(t("settings.minted"));
    } catch (err) {
      setMsg(err instanceof Error ? err.message : t("settings.mintFail"));
    }
  }

  async function createProject(e: FormEvent) {
    e.preventDefault();
    try {
      await api.createProject({ name: projName, slug: projSlug });
      setProjName("");
      setProjSlug("");
      setMsg(t("settings.projectCreated"));
      await reload();
    } catch (err) {
      setMsg(err instanceof Error ? err.message : t("settings.projectFail"));
    }
  }

  return (
    <div className="stack-gap">
      <div className="page-head">
        <div>
          <h1>{t("settings.title")}</h1>
          <p className="lead">{t("settings.lead")}</p>
        </div>
      </div>
      <ProjectPicker />
      <section className="panel stack-gap">
        <h2 style={{ margin: 0 }}>{t("settings.newProject")}</h2>
        <form className="row" onSubmit={createProject}>
          <div className="field">
            <label>{t("apps.name")}</label>
            <input value={projName} onChange={(e) => setProjName(e.target.value)} required />
          </div>
          <div className="field">
            <label>{t("apps.slug")}</label>
            <input
              value={projSlug}
              onChange={(e) => setProjSlug(e.target.value)}
              pattern="^[a-z0-9][a-z0-9\-]*$"
              required
            />
          </div>
          <button className="btn" type="submit">
            {t("settings.createProject")}
          </button>
        </form>
      </section>
      <section className="panel stack-gap">
        <p className="muted">{t("settings.hint")}</p>
        <button className="btn" type="button" onClick={mint}>
          {t("settings.mint")}
        </button>
        {msg ? <p className="muted">{msg}</p> : null}
        {secret ? <pre className="log-box">{secret}</pre> : null}
        {keys.length === 0 ? (
          <p className="muted">{t("settings.keysEmpty")}</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>{t("apps.name")}</th>
                <th>prefix</th>
                <th>{t("overview.when")}</th>
              </tr>
            </thead>
            <tbody>
              {keys.map((k) => (
                <tr key={k.id}>
                  <td>{k.name}</td>
                  <td>
                    <code>{k.key_prefix}</code>
                  </td>
                  <td className="muted">{new Date(k.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}

export default function App() {
  const auth = useAuth();
  const navigate = useNavigate();
  const { t } = useI18n();

  if (!auth.ready) {
    return (
      <div className="login-wrap">
        <p className="muted">{t("login.loadingSession")}</p>
      </div>
    );
  }

  if (!auth.loggedIn) {
    return (
      <LoginPage
        onLogin={(email) => {
          auth.setEmail(email);
          navigate("/");
        }}
      />
    );
  }

  return (
    <ProjectProvider>
    <Shell
      email={auth.email!}
      onLogout={() => {
        tokenStore.set(null);
        auth.setEmail(null);
      }}
    >
      <Routes>
        <Route path="/" element={<OverviewPage />} />
        <Route path="/apps" element={<AppsPage />} />
        <Route path="/jobs" element={<JobsPage />} />
        <Route path="/workers" element={<WorkersPage />} />
        <Route path="/schedules" element={<SchedulesPage />} />
        <Route path="/alerts" element={<AlertsPage />} />
        <Route path="/dlq" element={<DlqPage />} />
        <Route path="/secrets" element={<SecretsPage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/metrics" element={<MetricsPage />} />
        <Route path="/webhooks" element={<WebhooksPage />} />
        <Route path="/templates" element={<TemplatesPage />} />
        <Route path="/health" element={<HealthPage />} />
        <Route path="/ops" element={<OpsPage />} />
        <Route path="/scenarios" element={<ScenariosPage />} />
        <Route path="/audit" element={<AuditPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Shell>
    </ProjectProvider>
  );
}
