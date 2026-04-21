export function Panel({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <h3 className="panel-title">{title}</h3>
          {description ? <p className="muted-copy">{description}</p> : null}
        </div>
      </div>
      {children}
    </section>
  );
}
