export function JsonPanel({ title, data }) {
  return (
    <section className="panel">
      <h2>{title}</h2>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </section>
  );
}
