import { JsonPanel } from "../components/JsonPanel";
import { useCoreHealth } from "../hooks/useCoreHealth";
import { useApiConfig } from "../state/ApiConfigContext";

export function DashboardPage() {
  const { apiBase } = useApiConfig();
  const { loading, error, health } = useCoreHealth(apiBase);

  return (
    <section>
      <h2>Dashboard</h2>
      <p>Core API: {apiBase}</p>
      {loading && <p>Loading health...</p>}
      {error && <p className="error">{error}</p>}
      {health && <JsonPanel title="Health" data={health} />}
    </section>
  );
}
