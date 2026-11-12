const API_BASE = import.meta.env.VITE_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

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
  jobs: (projectId: string) =>
    request<
      Array<{
        id: string;
        name: string;
        status: string;
        queue: string;
        attempt: number;
        created_at: string;
        error: string | null;
      }>
    >(`/api/v1/projects/${projectId}/jobs`),
  createJob: (
    projectId: string,
    appId: string,
    body: { name: string; payload?: Record<string, unknown>; queue?: string },
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
};
