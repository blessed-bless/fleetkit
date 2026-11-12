import { useCallback, useEffect, useMemo, useState } from "react";
import type { FormEvent, ReactNode } from "react";
import { Link, Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { ApiError, api, tokenStore } from "./api";
import { AlertsPage } from "./pages/AlertsPage";
import { DlqPage } from "./pages/DlqPage";
import { SearchPage } from "./pages/SearchPage";
import { MetricsPage } from "./pages/MetricsPage";
import { SecretsPage } from "./pages/SecretsPage";

type Project = { id: string; slug: string; name: string; description: string };
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
  const links = [
    ["/", "Обзор"],
    ["/apps", "Apps"],
    ["/jobs", "Jobs"],
    ["/workers", "Workers"],
    ["/alerts", "Алерты"],
    ["/dlq", "DLQ"],
    ["/secrets", "Секреты"],
    ["/search", "Поиск"],
    ["/metrics", "Метрики"],
    ["/settings", "Ключи"],
  ] as const;

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          Fleet<span>Kit</span>
        </div>
        <nav className="side-nav">
          {links.map(([to, label]) => (
            <Link key={to} to={to} className={loc.pathname === to ? "active" : ""}>
              <span className="nav-dot" />
              {label}
            </Link>
          ))}
        </nav>
        <div className="side-foot">
          <span className="muted" style={{ fontSize: "0.85rem", padding: "0 8px" }}>
            {email}
          </span>
          <button className="btn ghost" type="button" onClick={onLogout}>
            Выйти
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
      setError(err instanceof ApiError ? err.message : "Не удалось войти");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-wrap">
      <form className="panel login-card stack-gap" onSubmit={submit}>
        <div>
          <div className="brand">
            Fleet<span>Kit</span>
          </div>
          <h1>Control plane</h1>
          <p className="muted">Боты, воркеры и cron — одна очередь, один экран.</p>
        </div>
        <div className="field">
          <label htmlFor="email">Email</label>
          <input id="email" value={email} onChange={(e) => setEmail(e.target.value)} />
        </div>
        <div className="field">
          <label htmlFor="password">Пароль</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        {error ? <p className="error">{error}</p> : null}
        <button className="btn" disabled={busy} type="submit">
          {busy ? "Проверяем..." : "Войти"}
        </button>
      </form>
    </div>
  );
}

function useProject() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .projects()
      .then((items) => {
        setProjects(items);
        if (items[0]) setProjectId(items[0].id);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Не загрузились проекты"));
  }, []);

  const project = useMemo(
    () => projects.find((p) => p.id === projectId) || null,
    [projects, projectId],
  );

  return { projects, project, projectId, setProjectId, error };
}

function ProjectPicker({
  projects,
  projectId,
  onChange,
}: {
  projects: Project[];
  projectId: string;
  onChange: (id: string) => void;
}) {
  return (
    <div className="field" style={{ maxWidth: 280 }}>
      <label htmlFor="project">Проект</label>
      <select id="project" value={projectId} onChange={(e) => onChange(e.target.value)}>
        {projects.map((p) => (
          <option key={p.id} value={p.id}>
            {p.name} ({p.slug})
          </option>
        ))}
      </select>
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
  const [data, setData] = useState<Awaited<ReturnType<typeof api.overview>> | null>(null);
  const [error, setError] = useState("");
  const [tick, setTick] = useState(0);

  useEffect(() => {
    let alive = true;
    api
      .overview()
      .then((d) => {
        if (alive) setData(d);
      })
      .catch((err) => {
        if (alive) setError(err instanceof Error ? err.message : "Обзор недоступен");
      });
    return () => {
      alive = false;
    };
  }, [tick]);

  useEffect(() => {
    const id = window.setInterval(() => setTick((t) => t + 1), 4000);
    return () => window.clearInterval(id);
  }, []);

  if (error) return <p className="error">{error}</p>;
  if (!data) return <p className="muted">Собираем статистику...</p>;

  return (
    <div className="stack-gap">
      <div className="page-head">
        <div>
          <h1>Обзор флота</h1>
          <p className="lead">Очередь, воркеры и свежие события. Обновляется каждые 4 сек.</p>
        </div>
        <span className="live-dot">
          <i /> live
        </span>
      </div>
      <div className="grid stats">
        <div className="stat">
          <div className="label">Проекты</div>
          <div className="value">{data.projects}</div>
        </div>
        <div className="stat">
          <div className="label">Apps</div>
          <div className="value">{data.apps}</div>
        </div>
        <div className="stat">
          <div className="label">Workers online</div>
          <div className="value">{data.workers_online}</div>
        </div>
        <div className="stat">
          <div className="label">Queued</div>
          <div className="value">{data.jobs_queued}</div>
        </div>
        <div className="stat">
          <div className="label">Running</div>
          <div className="value">{data.jobs_running}</div>
        </div>
        <div className="stat">
          <div className="label">Failed 24h</div>
          <div className="value">{data.jobs_failed_24h}</div>
        </div>
      </div>
      <section className="panel">
        <h2>Последние события</h2>
        {data.recent_events.length === 0 ? (
          <p className="muted">Пока тихо. Создай app и кинь первый job.</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Когда</th>
                <th>Тип</th>
                <th>Сообщение</th>
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
  const { projects, projectId, setProjectId, error } = useProject();
  const [apps, setApps] = useState<Awaited<ReturnType<typeof api.apps>>>([]);
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [kind, setKind] = useState("worker");
  const [msg, setMsg] = useState("");

  async function reload(id: string) {
    setApps(await api.apps(id));
  }

  useEffect(() => {
    if (projectId) reload(projectId).catch((err) => setMsg(err.message));
  }, [projectId]);

  async function create(e: FormEvent) {
    e.preventDefault();
    if (!projectId) return;
    setMsg("");
    try {
      await api.createApp(projectId, { name, slug, kind });
      setName("");
      setSlug("");
      await reload(projectId);
      setMsg("App создано");
    } catch (err) {
      setMsg(err instanceof Error ? err.message : "Не создалось");
    }
  }

  return (
    <div className="stack-gap">
      <div className="page-head">
        <div>
          <h1>Apps</h1>
          <p className="lead">Боты, воркеры, cron и webhook-приёмники в одном проекте.</p>
        </div>
      </div>
      {error ? <p className="error">{error}</p> : null}
      <ProjectPicker projects={projects} projectId={projectId} onChange={setProjectId} />
      <form className="panel row" onSubmit={create}>
        <div className="field">
          <label>Имя</label>
          <input value={name} onChange={(e) => setName(e.target.value)} required />
        </div>
        <div className="field">
          <label>Slug</label>
          <input
            value={slug}
            onChange={(e) => setSlug(e.target.value)}
            pattern="^[a-z0-9][a-z0-9\-]*$"
            required
          />
        </div>
        <div className="field">
          <label>Тип</label>
          <select value={kind} onChange={(e) => setKind(e.target.value)}>
            <option value="worker">worker</option>
            <option value="bot">bot</option>
            <option value="cron">cron</option>
            <option value="webhook">webhook</option>
          </select>
        </div>
        <button className="btn" type="submit">
          Создать app
        </button>
      </form>
      {msg ? <p className="muted">{msg}</p> : null}
      <section className="panel">
        {apps.length === 0 ? (
          <p className="muted">Здесь пока пусто. Добавь первое app под бота или воркер.</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Имя</th>
                <th>Slug</th>
                <th>Тип</th>
                <th>Статус</th>
                <th>ID</th>
              </tr>
            </thead>
            <tbody>
              {apps.map((app) => (
                <tr key={app.id}>
                  <td>{app.name}</td>
                  <td>{app.slug}</td>
                  <td>{app.kind}</td>
                  <td>
                    <span className={`badge ${app.is_enabled ? "ok" : "warn"}`}>
                      {app.is_enabled ? "enabled" : "disabled"}
                    </span>
                  </td>
                  <td className="muted">{app.id}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}

function JobsPage() {
  const { projects, projectId, setProjectId } = useProject();
  const [apps, setApps] = useState<Awaited<ReturnType<typeof api.apps>>>([]);
  const [jobs, setJobs] = useState<JobRow[]>([]);
  const [appId, setAppId] = useState("");
  const [filterApp, setFilterApp] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [filterQ, setFilterQ] = useState("");
  const [jobName, setJobName] = useState("ping");
  const [msg, setMsg] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [activeId, setActiveId] = useState<string | null>(null);
  const [detail, setDetail] = useState<JobRow | null>(null);
  const [logs, setLogs] = useState<Array<{ seq: number; stream: string; line: string }>>([]);
  const [live, setLive] = useState(true);

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
    if (!live) return;
    const id = window.setInterval(() => {
      reload().catch(() => undefined);
    }, 3000);
    return () => window.clearInterval(id);
  }, [live, reload]);

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
      await api.createJob(projectId, appId, { name: jobName, payload: { source: "dashboard" } });
      await reload();
      setMsg("Job в очереди");
    } catch (err) {
      setMsg(err instanceof Error ? err.message : "Не отправилось");
    }
  }

  async function cancelOne(id: string) {
    if (!projectId) return;
    await api.cancelJob(projectId, id);
    await reload();
    setMsg("Job отменён");
  }

  async function cancelSelected() {
    if (!projectId || selected.size === 0) return;
    await api.cancelJobsBulk(projectId, [...selected]);
    setSelected(new Set());
    await reload();
    setMsg(`Отменено: ${selected.size}`);
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
          <h1>Jobs</h1>
          <p className="lead">Фильтры, bulk-cancel, детали и логи. Live-обновление очереди.</p>
        </div>
        <button className="btn ghost" type="button" onClick={() => setLive((v) => !v)}>
          {live ? (
            <span className="live-dot">
              <i /> live on
            </span>
          ) : (
            "Включить live"
          )}
        </button>
      </div>
      <ProjectPicker projects={projects} projectId={projectId} onChange={setProjectId} />

      <form className="panel row" onSubmit={enqueue}>
        <div className="field">
          <label>App</label>
          <select value={appId} onChange={(e) => setAppId(e.target.value)}>
            {apps.map((a) => (
              <option key={a.id} value={a.id}>
                {a.name}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label>Имя job</label>
          <input value={jobName} onChange={(e) => setJobName(e.target.value)} required />
        </div>
        <button className="btn" type="submit" disabled={!appId}>
          Поставить в очередь
        </button>
      </form>

      <div className="panel toolbar">
        <div className="field">
          <label>Статус</label>
          <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
            <option value="">все</option>
            <option value="queued">queued</option>
            <option value="running">running</option>
            <option value="succeeded">succeeded</option>
            <option value="failed">failed</option>
            <option value="cancelled">cancelled</option>
          </select>
        </div>
        <div className="field">
          <label>App</label>
          <select value={filterApp} onChange={(e) => setFilterApp(e.target.value)}>
            <option value="">все</option>
            {apps.map((a) => (
              <option key={a.id} value={a.id}>
                {a.name}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label>Поиск по имени</label>
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
          Отменить выбранные ({selected.size})
        </button>
      </div>

      {msg ? <p className="muted">{msg}</p> : null}

      <div className="split">
        <section className="panel">
          <table className="table">
            <thead>
              <tr>
                <th />
                <th>Имя</th>
                <th>Статус</th>
                <th>Queue</th>
                <th>Attempt</th>
                <th>Создан</th>
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
                        Отменить
                      </button>
                    ) : null}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {jobs.length === 0 ? (
            <p className="muted">Очередь пустая или фильтр ничего не поймал.</p>
          ) : null}
        </section>

        <aside className="panel drawer stack-gap">
          <h2>Детали</h2>
          {!detail ? (
            <p className="muted">Кликни job слева — покажем payload, результат и логи.</p>
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
                <label>Payload</label>
                <pre className="log-box">{JSON.stringify(detail.payload, null, 2)}</pre>
              </div>
              {detail.result ? (
                <div className="field">
                  <label>Result</label>
                  <pre className="log-box">{JSON.stringify(detail.result, null, 2)}</pre>
                </div>
              ) : null}
              <div className="field">
                <label>Логи</label>
                <div className="log-box">
                  {logs.length === 0 ? (
                    <span className="muted">Логов пока нет</span>
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
  const { projects, projectId, setProjectId } = useProject();
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
          <h1>Workers</h1>
          <p className="lead">Кто онлайн и когда был последний heartbeat.</p>
        </div>
        <span className="live-dot">
          <i /> live
        </span>
      </div>
      <ProjectPicker projects={projects} projectId={projectId} onChange={setProjectId} />
      <section className="panel">
        {workers.length === 0 ? (
          <p className="muted">Нет воркеров. Подними examples/http-worker или docker worker.</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Имя</th>
                <th>Host</th>
                <th>Статус</th>
                <th>Heartbeat</th>
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
                      : "ещё не было"}
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

function AlertsRoute() {
  const { projects, projectId, setProjectId } = useProject();
  return (
    <AlertsPage projects={projects} projectId={projectId} onProjectChange={setProjectId} />
  );
}

function DlqRoute() {
  const { projects, projectId, setProjectId } = useProject();
  return <DlqPage projects={projects} projectId={projectId} onProjectChange={setProjectId} />;
}

function SecretsRoute() {
  const { projects, projectId, setProjectId } = useProject();
  return (
    <SecretsPage projects={projects} projectId={projectId} onProjectChange={setProjectId} />
  );
}

function SearchRoute() {
  const { projects, projectId, setProjectId } = useProject();
  return (
    <SearchPage projects={projects} projectId={projectId} onProjectChange={setProjectId} />
  );
}

function MetricsRoute() {
  const { projects, projectId, setProjectId } = useProject();
  return (
    <MetricsPage projects={projects} projectId={projectId} onProjectChange={setProjectId} />
  );
}

function SettingsPage() {
  const { projects, projectId, setProjectId } = useProject();
  const [secret, setSecret] = useState("");
  const [msg, setMsg] = useState("");

  async function mint() {
    if (!projectId) return;
    try {
      const key = await api.createApiKey(projectId, `key-${Date.now()}`);
      setSecret(key.secret);
      setMsg("Ключ создан. Скопируй сейчас — потом его не покажем.");
    } catch (err) {
      setMsg(err instanceof Error ? err.message : "Не выпустился ключ");
    }
  }

  return (
    <div className="stack-gap">
      <div className="page-head">
        <div>
          <h1>API-ключи</h1>
          <p className="lead">Для воркеров и агентов. Один раз видишь secret — и всё.</p>
        </div>
      </div>
      <ProjectPicker projects={projects} projectId={projectId} onChange={setProjectId} />
      <section className="panel stack-gap">
        <p className="muted">
          Клади ключ в <code>X-FleetKit-Key</code> или в SDK. Не коммить в git.
        </p>
        <button className="btn" type="button" onClick={mint}>
          Выпустить ключ
        </button>
        {msg ? <p className="muted">{msg}</p> : null}
        {secret ? <pre className="log-box">{secret}</pre> : null}
      </section>
    </div>
  );
}

export default function App() {
  const auth = useAuth();
  const navigate = useNavigate();

  if (!auth.ready) {
    return (
      <div className="login-wrap">
        <p className="muted">Загружаем сессию...</p>
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
        <Route path="/alerts" element={<AlertsRoute />} />
        <Route path="/dlq" element={<DlqRoute />} />
        <Route path="/secrets" element={<SecretsRoute />} />
        <Route path="/search" element={<SearchRoute />} />
        <Route path="/metrics" element={<MetricsRoute />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Shell>
  );
}
