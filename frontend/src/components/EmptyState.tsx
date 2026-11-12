export function EmptyState({ title, hint }: { title: string; hint: string }) {
  return (
    <div>
      <p style={{ marginBottom: 4, fontWeight: 600 }}>{title}</p>
      <p className="muted" style={{ marginTop: 0 }}>
        {hint}
      </p>
    </div>
  );
}
