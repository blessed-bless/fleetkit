import { useEffect, useRef, useState } from "react";
import { api, tokenStore } from "../api";

export type LiveEvent = {
  kind: string;
  project_id?: string;
  payload?: Record<string, unknown>;
};

/** WebSocket live feed with reconnect. Falls back to silent idle if WS dies. */
export function useLiveProject(projectId: string | null, onEvent?: (ev: LiveEvent) => void) {
  const [connected, setConnected] = useState(false);
  const [lastKind, setLastKind] = useState<string | null>(null);
  const cb = useRef(onEvent);
  cb.current = onEvent;

  useEffect(() => {
    if (!projectId) return;
    const token = tokenStore.get();
    if (!token) return;

    let closed = false;
    let sock: WebSocket | null = null;
    let timer: number | undefined;
    let attempt = 0;

    const base = api.baseUrl.replace(/^http/, "ws");

    function connect() {
      if (closed) return;
      sock = new WebSocket(`${base}/api/v1/ws/projects/${projectId}?token=${encodeURIComponent(token!)}`);
      sock.onopen = () => {
        attempt = 0;
        setConnected(true);
      };
      sock.onclose = () => {
        setConnected(false);
        if (closed) return;
        attempt += 1;
        const delay = Math.min(8000, 500 * 2 ** Math.min(attempt, 4));
        timer = window.setTimeout(connect, delay);
      };
      sock.onerror = () => {
        sock?.close();
      };
      sock.onmessage = (msg) => {
        try {
          const data = JSON.parse(msg.data) as LiveEvent;
          if (data.kind === "ping" || data.kind === "hello") return;
          setLastKind(data.kind);
          cb.current?.(data);
        } catch {
          /* ignore malformed */
        }
      };
    }

    connect();
    return () => {
      closed = true;
      if (timer) window.clearTimeout(timer);
      sock?.close();
    };
  }, [projectId]);

  return { connected, lastKind };
}
