import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";
import { api } from "../api";
import { useLiveProject } from "../hooks/useLive";
import { useI18n } from "../i18n";
import { ProjectPicker, useProject } from "../project";

type JobRow = Awaited<ReturnType<typeof api.jobs>>[number];

function statusBadge(status: string) {
  if (status === "succeeded") return "ok";
  if (status === "failed" || status === "timed_out") return "err";
  if (status === "running") return "run";
  if (status === "queued" || status === "cancelled") return "warn";
  return "";
}

export function JobsPage() {
  const { t } = useI18n();
  const { projectId } = useProject();
  const [apps, setApps] = useState<Awaited<ReturnType<typeof api.apps>>>([]);
  const [jobs, setJobs] = useState<JobRow[]>([]);
  const [appId, setAppId] = useState("");
  const [filterApp, setFilterApp] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [filterQ, setFilterQ] = useState("");
  const [jobName, setJobName] = useState("ping");
  const [jobTags, setJobTags] = useState("");
  const [batchCount, setBatchCount] = useState(1);
  const [chainNames, setChainNames] = useState("fetch,transform,publish");
  const [priority, setPriority] = useState(50);
  const [msg, setMsg] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [activeId, setActiveId] = useState<string | null>(null);
  const [detail, setDetail] = useState<JobRow | null>(null);
  const [deps, setDeps] = useState<Array<{ id: string; depends_on_job_id: string }>>([]);
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
    Promise.all([
      api.job(projectId, activeId),
      api.jobLogs(projectId, activeId),
      api.jobDependencies(projectId, activeId),
    ])
      .then(([j, l, d]) => {
        if (!alive) return;
        setDetail({ ...j, tags: j.tags || [] });
        setLogs(l.map((x) => ({ seq: x.seq, stream: x.stream, line: x.line })));
        setDeps(d.map((x) => ({ id: x.id, depends_on_job_id: x.depends_on_job_id })));
        if (typeof j.priority === "number") setPriority(j.priority);
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
      const tags = jobTags
        .split(",")
        .map((x) => x.trim())
        .filter(Boolean);
      const n = Math.max(1, Math.min(100, Number(batchCount) || 1));
      if (n === 1) {
        await api.createJob(projectId, appId, {
          name: jobName,
          payload: { source: "dashboard" },
          tags,
        });
        setMsg(t("jobs.queuedMsg"));
      } else {
        const res = await api.batchJobs(projectId, {
          app_id: appId,
          name: jobName,
          payloads: Array.from({ length: n }, (_, i) => ({ source: "dashboard", i, tags })),
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

  async function retryOne(id: string) {
    if (!projectId) return;
    await api.retryJob(projectId, id);
    await reload();
    setMsg(t("jobs.retried"));
  }

  async function cloneOne(id: string) {
    if (!projectId) return;
    await api.cloneJob(projectId, id);
    await reload();
    setMsg(t("jobs.cloned"));
  }

  async function enqueueChain(e: FormEvent) {
    e.preventDefault();
    if (!projectId || !appId) return;
    const names = chainNames
      .split(",")
      .map((x) => x.trim())
      .filter(Boolean);
    if (names.length < 2) {
      setMsg(t("jobs.chainNeedTwo"));
      return;
    }
    try {
      const res = await api.enqueueChain(projectId, appId, {
        names,
        payload: { source: "dashboard-chain" },
        tags: jobTags
          .split(",")
          .map((x) => x.trim())
          .filter(Boolean),
      });
      setMsg(t("jobs.chainQueued", { n: res.count }));
      await reload();
    } catch (err) {
      setMsg(err instanceof Error ? err.message : t("jobs.enqueueFail"));
    }
  }

  async function savePriority() {
    if (!projectId || !activeId) return;
    await api.setJobPriority(projectId, activeId, priority);
    await reload();
    setMsg(t("jobs.prioritySaved", { n: priority }));
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
          <label>{t("jobs.tags")}</label>
          <input
            value={jobTags}
            onChange={(e) => setJobTags(e.target.value)}
            placeholder="demo,smoke"
          />
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

      <form className="panel row" onSubmit={enqueueChain}>
        <div className="field" style={{ flex: 1 }}>
          <label>{t("jobs.chain")}</label>
          <input
            value={chainNames}
            onChange={(e) => setChainNames(e.target.value)}
            placeholder="fetch,transform,publish"
          />
        </div>
        <button className="btn ghost" type="submit" disabled={!appId}>
          {t("jobs.enqueueChain")}
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
                    {job.status === "failed" ||
                    job.status === "cancelled" ||
                    job.status === "timed_out" ? (
                      <button
                        className="btn ghost"
                        type="button"
                        onClick={() => retryOne(job.id).catch((err) => setMsg(err.message))}
                      >
                        {t("jobs.retry")}
                      </button>
                    ) : null}
                    <button
                      className="btn ghost"
                      type="button"
                      onClick={() => cloneOne(job.id).catch((err) => setMsg(err.message))}
                    >
                      {t("jobs.clone")}
                    </button>
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
                {detail.blocked ? (
                  <span className="badge warn" style={{ marginLeft: 6 }}>
                    {t("jobs.blocked")}
                  </span>
                ) : null}
              </div>
              <p className="muted" style={{ margin: 0, fontSize: "0.85rem" }}>
                {detail.id}
              </p>
              {detail.error ? <p className="error">{detail.error}</p> : null}
              <div className="field row" style={{ alignItems: "end", gap: 8 }}>
                <div className="field" style={{ margin: 0 }}>
                  <label>{t("jobs.priority")}</label>
                  <input
                    type="number"
                    min={0}
                    max={100}
                    value={priority}
                    onChange={(e) => setPriority(Number(e.target.value))}
                  />
                </div>
                <button
                  className="btn ghost"
                  type="button"
                  onClick={() => savePriority().catch((err) => setMsg(err.message))}
                >
                  {t("jobs.savePriority")}
                </button>
              </div>
              <div className="field">
                <label>{t("jobs.deps")}</label>
                {deps.length === 0 ? (
                  <p className="muted" style={{ margin: 0 }}>
                    {t("jobs.depsEmpty")}
                  </p>
                ) : (
                  <ul style={{ margin: 0, paddingLeft: "1.1rem" }}>
                    {deps.map((d) => (
                      <li key={d.id}>
                        <button
                          className="btn ghost"
                          type="button"
                          onClick={() => setActiveId(d.depends_on_job_id)}
                        >
                          {d.depends_on_job_id.slice(0, 8)}…
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
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
