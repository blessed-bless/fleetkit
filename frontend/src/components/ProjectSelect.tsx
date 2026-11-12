import type { Project } from "../hooks/useProjectId";

export function ProjectSelect({
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
      <label htmlFor="project-select">Проект</label>
      <select
        id="project-select"
        value={projectId}
        onChange={(e) => onChange(e.target.value)}
      >
        {projects.map((p) => (
          <option key={p.id} value={p.id}>
            {p.name} ({p.slug})
          </option>
        ))}
      </select>
    </div>
  );
}
