const API_BASE =
  import.meta.env.VITE_API_URL?.replace(/\/$/, "") ||
  `${window.location.protocol}//${window.location.hostname}:8000`;

export const tokenStore = {
  get: () => localStorage.getItem("fleetkit_token"),
  set: (token: string | null) => {
    if (token) localStorage.setItem("fleetkit_token", token);
    else localStorage.removeItem("fleetkit_token");
  },
};

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers || {});
  headers.set("Content-Type", "application/json");
  const token = tokenStore.get();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const resp = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!resp.ok) {
    let detail: unknown = `HTTP ${resp.status}`;
    try {
      const body = await resp.json();
      detail = body.detail || JSON.stringify(body);
    } catch {
      /* ignore */
    }
    throw new ApiError(resp.status, typeof detail === "string" ? detail : "Ошибка API");
  }
  if (resp.status === 204) return undefined as T;
  return resp.json() as Promise<T>;
}

export const api = {
  baseUrl: API_BASE,
  login: (email: string, password: string) =>
    request<{ access_token: string }>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  me: () => request<{ id: string; email: string; display_name: string }>("/api/v1/auth/me"),
  overview: () =>
    request<{
      projects: number;
      apps: number;
      workers_online: number;
      jobs_queued: number;
      jobs_running: number;
      jobs_failed_24h: number;
      recent_events: Array<{
        id: string;
        level: string;
        kind: string;
        message: string;
        created_at: string;
      }>;
    }>("/api/v1/overview"),
  projects: () =>
    request<Array<{ id: string; slug: string; name: string; description: string }>>(
      "/api/v1/projects",
    ),
  createProject: (body: { name: string; slug: string; description?: string }) =>
    request<{ id: string; slug: string; name: string; description: string }>(
      "/api/v1/projects",
      { method: "POST", body: JSON.stringify(body) },
    ),
  apiKeys: (projectId: string) =>
    request<Array<{ id: string; name: string; key_prefix: string; created_at: string }>>(
      `/api/v1/projects/${projectId}/api-keys`,
    ),
  apps: (projectId: string) =>
    request<
      Array<{
        id: string;
        slug: string;
        name: string;
        kind: string;
        is_enabled: boolean;
        created_at: string;
      }>
    >(`/api/v1/projects/${projectId}/apps`),
  createApp: (projectId: string, body: { name: string; slug: string; kind: string }) =>
    request(`/api/v1/projects/${projectId}/apps`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  patchApp: (
    projectId: string,
    appId: string,
    body: { name?: string; is_enabled?: boolean; config?: Record<string, unknown> },
  ) =>
    request(`/api/v1/projects/${projectId}/apps/${appId}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  webhooks: (projectId: string) =>
    request<
      Array<{
        id: string;
        app_id: string;
        name: string;
        path_token: string;
        secret: string;
        target_job_name: string;
        is_enabled: boolean;
        created_at: string;
        ingest_path: string | null;
      }>
    >(`/api/v1/projects/${projectId}/webhooks`),
  createWebhook: (
    projectId: string,
    appId: string,
    body: { name: string; target_job_name?: string },
  ) =>
    request<{
      id: string;
      secret: string;
      ingest_path: string | null;
      target_job_name: string;
      name: string;
      is_enabled: boolean;
    }>(`/api/v1/projects/${projectId}/apps/${appId}/webhooks`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  jobs: (
    projectId: string,
    params?: {
      app_id?: string;
      status?: string;
      queue?: string;
      tag?: string;
      q?: string;
      limit?: number;
    },
  ) => {
    const qs = new URLSearchParams();
    if (params?.app_id) qs.set("app_id", params.app_id);
    if (params?.status) qs.set("status", params.status);
    if (params?.queue) qs.set("queue", params.queue);
    if (params?.tag) qs.set("tag", params.tag);
    if (params?.q) qs.set("q", params.q);
    if (params?.limit) qs.set("limit", String(params.limit));
    const suffix = qs.toString() ? `?${qs}` : "";
    return request<
      Array<{
        id: string;
        app_id: string;
        name: string;
        status: string;
        queue: string;
        tags?: string[];
        attempt: number;
        max_attempts: number;
        payload: Record<string, unknown>;
        result: Record<string, unknown> | null;
        created_at: string;
        started_at: string | null;
        finished_at: string | null;
        error: string | null;
        priority?: number | null;
        blocked?: boolean | null;
      }>
    >(`/api/v1/projects/${projectId}/jobs${suffix}`);
  },
  job: (projectId: string, jobId: string) =>
    request<{
      id: string;
      app_id: string;
      name: string;
      status: string;
      queue: string;
      tags?: string[];
      attempt: number;
      max_attempts: number;
      payload: Record<string, unknown>;
      result: Record<string, unknown> | null;
      created_at: string;
      started_at: string | null;
      finished_at: string | null;
      error: string | null;
      priority?: number | null;
      blocked?: boolean | null;
    }>(`/api/v1/projects/${projectId}/jobs/${jobId}`),
  jobLogs: (projectId: string, jobId: string, afterSeq = 0) =>
    request<Array<{ id: string; seq: number; stream: string; line: string; created_at: string }>>(
      `/api/v1/projects/${projectId}/jobs/${jobId}/logs?after_seq=${afterSeq}`,
    ),
  cancelJob: (projectId: string, jobId: string) =>
    request(`/api/v1/projects/${projectId}/jobs/${jobId}/cancel`, { method: "POST" }),
  retryJob: (projectId: string, jobId: string) =>
    request(`/api/v1/projects/${projectId}/jobs/${jobId}/retry`, { method: "POST" }),
  cloneJob: (
    projectId: string,
    jobId: string,
    body?: { name?: string; copy_tags?: boolean; payload?: Record<string, unknown> },
  ) =>
    request(`/api/v1/projects/${projectId}/jobs/${jobId}/clone`, {
      method: "POST",
      body: JSON.stringify(body || { copy_tags: true }),
    }),
  setJobPriority: (projectId: string, jobId: string, priority: number) =>
    request(`/api/v1/projects/${projectId}/jobs/${jobId}/priority`, {
      method: "PUT",
      body: JSON.stringify({ priority }),
    }),
  jobDependencies: (projectId: string, jobId: string) =>
    request<Array<{ id: string; job_id: string; depends_on_job_id: string; created_at: string }>>(
      `/api/v1/projects/${projectId}/jobs/${jobId}/dependencies`,
    ),
  addJobDependency: (projectId: string, jobId: string, dependsOnJobId: string) =>
    request(`/api/v1/projects/${projectId}/jobs/${jobId}/dependencies`, {
      method: "POST",
      body: JSON.stringify({ depends_on_job_id: dependsOnJobId }),
    }),
  enqueueChain: (
    projectId: string,
    appId: string,
    body: { names: string[]; payload?: Record<string, unknown>; queue?: string; tags?: string[] },
  ) =>
    request<{ job_ids: string[]; count: number }>(
      `/api/v1/projects/${projectId}/apps/${appId}/jobs/chain`,
      { method: "POST", body: JSON.stringify(body) },
    ),
  cancelJobsBulk: (projectId: string, jobIds: string[]) =>
    request(`/api/v1/projects/${projectId}/jobs/cancel-bulk`, {
      method: "POST",
      body: JSON.stringify({ job_ids: jobIds }),
    }),
  createJob: (
    projectId: string,
    appId: string,
    body: {
      name: string;
      payload?: Record<string, unknown>;
      queue?: string;
      tags?: string[];
      priority?: number;
      depends_on_job_id?: string;
    },
  ) =>
    request(`/api/v1/projects/${projectId}/apps/${appId}/jobs`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  workers: (projectId: string) =>
    request<
      Array<{
        id: string;
        name: string;
        hostname: string;
        status: string;
        last_heartbeat_at: string | null;
      }>
    >(`/api/v1/projects/${projectId}/workers`),
  drainWorker: (projectId: string, workerId: string, draining = true) =>
    request(`/api/v1/projects/${projectId}/workers/${workerId}/drain`, {
      method: "POST",
      body: JSON.stringify({ draining }),
    }),
  createApiKey: (projectId: string, name: string) =>
    request<{ id: string; secret: string; key_prefix: string }>(
      `/api/v1/projects/${projectId}/api-keys`,
      { method: "POST", body: JSON.stringify({ name }) },
    ),
  schedules: (projectId: string) =>
    request<
      Array<{
        id: string;
        name: string;
        cron: string;
        is_enabled: boolean;
        next_run_at: string | null;
      }>
    >(`/api/v1/projects/${projectId}/schedules`),
  createSchedule: (
    projectId: string,
    appId: string,
    body: { name: string; cron: string; payload?: Record<string, unknown> },
  ) =>
    request(`/api/v1/projects/${projectId}/apps/${appId}/schedules`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  patchSchedule: (
    projectId: string,
    scheduleId: string,
    body: { is_enabled?: boolean; cron?: string; name?: string },
  ) =>
    request(`/api/v1/projects/${projectId}/schedules/${scheduleId}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  alertRules: (projectId: string) =>
    request<Array<{ id: string; name: string; expression: string; severity: string }>>(
      `/api/v1/projects/${projectId}/alert-rules`,
    ),
  alertFires: (projectId: string) =>
    request<Array<{ id: string; message: string; created_at: string }>>(
      `/api/v1/projects/${projectId}/alert-fires`,
    ),
  createAlertRule: (
    projectId: string,
    body: { name: string; expression: string; severity?: string },
  ) =>
    request(`/api/v1/projects/${projectId}/alert-rules`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  evaluateAlerts: (projectId: string) =>
    request<{ fired: number }>(`/api/v1/projects/${projectId}/alerts/evaluate`, {
      method: "POST",
    }),
  channels: (projectId: string) =>
    request<
      Array<{ id: string; name: string; kind: string; is_enabled: boolean; config: Record<string, unknown> }>
    >(`/api/v1/projects/${projectId}/channels`),
  createChannel: (
    projectId: string,
    body: { name: string; kind: string; config?: Record<string, unknown> },
  ) =>
    request(`/api/v1/projects/${projectId}/channels`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  deadLetters: (projectId: string) =>
    request<
      Array<{ id: string; job_name: string; error: string; attempts: number; requeued: boolean }>
    >(`/api/v1/projects/${projectId}/dead-letters`),
  requeueDeadLetter: (projectId: string, dlqId: string) =>
    request<{ job_id: string }>(`/api/v1/projects/${projectId}/dead-letters/${dlqId}/requeue`, {
      method: "POST",
    }),
  secrets: (projectId: string) =>
    request<Array<{ id: string; name: string; description: string }>>(
      `/api/v1/projects/${projectId}/secrets`,
    ),
  upsertSecret: (
    projectId: string,
    body: { name: string; value: string; description?: string },
  ) =>
    request(`/api/v1/projects/${projectId}/secrets`, {
      method: "PUT",
      body: JSON.stringify(body),
    }),
  revealSecret: (projectId: string, name: string) =>
    request<{ name: string; value: string }>(
      `/api/v1/projects/${projectId}/secrets/${encodeURIComponent(name)}/reveal`,
    ),
  search: (projectId: string, q: string) =>
    request<Record<string, unknown>>(
      `/api/v1/projects/${projectId}/search?q=${encodeURIComponent(q)}`,
    ),
  snapshotMetrics: (projectId: string) =>
    request<Record<string, number>>(`/api/v1/projects/${projectId}/metrics/snapshot`, {
      method: "POST",
    }),
  healthChecks: (projectId: string) =>
    request<
      Array<{
        id: string;
        app_id: string;
        name: string;
        kind: string;
        target: string;
        interval_seconds: number;
        timeout_seconds: number;
        is_enabled: boolean;
        last_status: string;
        last_checked_at: string | null;
        last_error: string;
      }>
    >(`/api/v1/projects/${projectId}/health-checks`),
  createHealthCheck: (
    projectId: string,
    body: {
      app_id: string;
      name: string;
      kind?: string;
      target?: string;
      interval_seconds?: number;
      timeout_seconds?: number;
    },
  ) =>
    request(`/api/v1/projects/${projectId}/health-checks`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  runHealthCheck: (projectId: string, checkId: string) =>
    request(`/api/v1/projects/${projectId}/health-checks/${checkId}/run`, {
      method: "POST",
    }),
  templates: (projectId: string) =>
    request<
      Array<{
        id: string;
        app_id: string;
        slug: string;
        name: string;
        job_name: string;
        queue: string;
        priority: number;
        payload: Record<string, unknown>;
        max_attempts: number;
        timeout_seconds: number;
      }>
    >(`/api/v1/projects/${projectId}/templates`),
  createTemplate: (
    projectId: string,
    body: {
      app_id: string;
      slug: string;
      name: string;
      job_name: string;
      queue?: string;
      priority?: number;
      payload?: Record<string, unknown>;
    },
  ) =>
    request(`/api/v1/projects/${projectId}/templates`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  runTemplate: (projectId: string, templateId: string) =>
    request<{ job_id: string }>(`/api/v1/projects/${projectId}/templates/${templateId}/run`, {
      method: "POST",
    }),
  retention: (projectId: string) =>
    request<Array<{ id: string; kind: string; keep_days: number; is_enabled: boolean }>>(
      `/api/v1/projects/${projectId}/retention`,
    ),
  patchRetention: (
    projectId: string,
    kind: string,
    body: { keep_days: number; is_enabled: boolean },
  ) =>
    request(`/api/v1/projects/${projectId}/retention/${encodeURIComponent(kind)}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  runRetention: (projectId: string) =>
    request<Record<string, number>>(`/api/v1/projects/${projectId}/retention/run`, {
      method: "POST",
    }),
  flags: (projectId: string) =>
    request<
      Array<{ id: string; key: string; enabled: boolean; payload: Record<string, unknown> }>
    >(`/api/v1/projects/${projectId}/flags`),
  upsertFlag: (projectId: string, body: { key: string; enabled: boolean }) =>
    request(`/api/v1/projects/${projectId}/flags`, {
      method: "PUT",
      body: JSON.stringify(body),
    }),
  audit: (projectId: string) =>
    request<
      Array<{
        id: string;
        action: string;
        resource_type: string;
        resource_id: string;
        created_at: string;
      }>
    >(`/api/v1/projects/${projectId}/audit`),
  appEnv: (projectId: string, appId: string) =>
    request<
      Array<{ id: string; key: string; is_secret: boolean; value_preview: string }>
    >(`/api/v1/projects/${projectId}/apps/${appId}/env`),
  upsertAppEnv: (
    projectId: string,
    appId: string,
    body: { key: string; value: string; is_secret?: boolean },
  ) =>
    request(`/api/v1/projects/${projectId}/apps/${appId}/env`, {
      method: "PUT",
      body: JSON.stringify(body),
    }),
  members: (projectId: string) =>
    request<
      Array<{ id: string; user_id: string; email?: string | null; role: string; created_at: string }>
    >(`/api/v1/projects/${projectId}/members`),
  updateMemberRole: (projectId: string, memberId: string, role: string) =>
    request(`/api/v1/projects/${projectId}/members/${memberId}`, {
      method: "PATCH",
      body: JSON.stringify({ role }),
    }),
  removeMember: (projectId: string, memberId: string) =>
    request(`/api/v1/projects/${projectId}/members/${memberId}`, { method: "DELETE" }),
  createInvite: (projectId: string, body: { email: string; role?: string }) =>
    request<{ id: string; email: string; role: string; token: string }>(
      `/api/v1/projects/${projectId}/invites`,
      { method: "POST", body: JSON.stringify(body) },
    ),
  projectInvites: (projectId: string) =>
    request<
      Array<{ id: string; email: string; role: string; token: string; accepted: boolean; created_at: string }>
    >(`/api/v1/projects/${projectId}/invites`),
  myInvites: () =>
    request<
      Array<{
        id: string;
        project_id?: string;
        email: string;
        role: string;
        token: string;
        accepted: boolean;
      }>
    >(`/api/v1/me/invites`),
  acceptInvite: (token: string) =>
    request(`/api/v1/invites/${encodeURIComponent(token)}/accept`, { method: "POST" }),
  batchJobs: (
    projectId: string,
    body: { app_id: string; name: string; payloads: Array<Record<string, unknown>> },
  ) =>
    request<{ count: number; job_ids: string[] }>(`/api/v1/projects/${projectId}/jobs/batch`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  quotas: (projectId: string) =>
    request<Record<string, unknown>>(`/api/v1/projects/${projectId}/quotas`),
  exportProject: (projectId: string) =>
    request<Record<string, unknown>>(`/api/v1/projects/${projectId}/export`),
  importProject: (projectId: string, body: Record<string, unknown>) =>
    request<Record<string, number>>(`/api/v1/projects/${projectId}/import`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  scenarios: () => request<Array<Record<string, string>>>("/api/v1/scenarios"),
  scenario: (name: string) =>
    request<Record<string, unknown>>(`/api/v1/scenarios/${encodeURIComponent(name)}`),
};
