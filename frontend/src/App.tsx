import { useEffect, useState } from "react";
import type { FormEvent, ReactNode } from "react";
import { Link, Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { ApiError, api, tokenStore } from "./api";
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
import { OverviewPage } from "./pages/OverviewPage";
import { AppsPage } from "./pages/AppsPage";
import { JobsPage } from "./pages/JobsPage";
import { WorkersPage } from "./pages/WorkersPage";
import { SettingsPage } from "./pages/SettingsPage";
import { ProjectProvider } from "./project";


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
