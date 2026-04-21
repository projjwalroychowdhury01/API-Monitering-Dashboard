export function MetricCard({
  label,
  value,
  helper,
}: {
  label: string;
  value: string;
  helper: string;
}) {
  return (
    <article className="metric-card">
      <p className="eyebrow">{label}</p>
      <strong className="metric-value">{value}</strong>
      <p className="muted-copy">{helper}</p>
    </article>
  );
}
