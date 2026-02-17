import { useEffect, useState } from "react";
import { getHealth } from "../api/reachApi";

export function useCoreHealth(apiBase) {
  const [loading, setLoading] = useState(true);
  const [health, setHealth] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadHealth() {
      setLoading(true);
      setError("");
      try {
        const result = await getHealth(apiBase);
        setHealth(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load health.");
      } finally {
        setLoading(false);
      }
    }

    loadHealth();
  }, [apiBase]);

  return { loading, health, error };
}
