import { useEffect, useState } from "react";
import { JsonPanel } from "../components/JsonPanel";
import { listRoutes } from "../api/reachApi";
import { useApiConfig } from "../state/ApiConfigContext";

export function PluginsPage() {
  const { apiBase } = useApiConfig();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [routes, setRoutes] = useState(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError("");
      try {
        const data = await listRoutes(apiBase);
        setRoutes(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load data.");
      } finally {
        setLoading(false);
      }
    }

    load();
  }, [apiBase]);

  return (
    <section>
      <h2>Plugin Studio</h2>
      <p>Placeholder page for Forge/IFTTT plugin manager.</p>
      {loading && <p>Loading data...</p>}
      {error && <p className="error">{error}</p>}
      {routes && <JsonPanel title="Current Routes" data={routes} />}
    </section>
  );
}
