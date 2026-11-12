import { useEffect, useMemo, useState } from "react";
import { api } from "../api";

export type Project = { id: string; slug: string; name: string; description: string };

export function useProjectId() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .projects()
      .then((items) => {
        setProjects(items as Project[]);
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
