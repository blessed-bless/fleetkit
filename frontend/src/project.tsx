import { createContext, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { api } from "./api";
import { useI18n } from "./i18n";

export type Project = { id: string; slug: string; name: string; description: string };

type Ctx = {
  projects: Project[];
  project: Project | null;
  projectId: string;
  setProjectId: (id: string) => void;
  error: string;
  loading: boolean;
  reload: () => Promise<void>;
};

const ProjectCtx = createContext<Ctx | null>(null);
const STORAGE_KEY = "fleetkit_project_id";

export function ProjectProvider({ children }: { children: ReactNode }) {
  const { t } = useI18n();
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectIdState] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  async function reload() {
    setLoading(true);
    try {
      const items = await api.projects();
      setProjects(items);
      const saved = localStorage.getItem(STORAGE_KEY) || "";
      const next = items.find((p) => p.id === saved)?.id || items[0]?.id || "";
      setProjectIdState(next);
      if (next) localStorage.setItem(STORAGE_KEY, next);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : t("project.loadFail"));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function setProjectId(id: string) {
    setProjectIdState(id);
    if (id) localStorage.setItem(STORAGE_KEY, id);
  }

  const project = useMemo(
    () => projects.find((p) => p.id === projectId) || null,
    [projects, projectId],
  );

  const value = useMemo(
    () => ({ projects, project, projectId, setProjectId, error, loading, reload }),
    [projects, project, projectId, error, loading],
  );

  return <ProjectCtx.Provider value={value}>{children}</ProjectCtx.Provider>;
}

export function useProject() {
  const ctx = useContext(ProjectCtx);
  if (!ctx) throw new Error("useProject outside ProjectProvider");
  return ctx;
}

export function ProjectPicker() {
  const { t } = useI18n();
  const { projects, projectId, setProjectId } = useProject();
  return (
    <div className="field" style={{ maxWidth: 280 }}>
      <label htmlFor="project">{t("project.label")}</label>
      <select id="project" value={projectId} onChange={(e) => setProjectId(e.target.value)}>
        {projects.map((p) => (
          <option key={p.id} value={p.id}>
            {p.name} ({p.slug})
          </option>
        ))}
      </select>
    </div>
  );
}
