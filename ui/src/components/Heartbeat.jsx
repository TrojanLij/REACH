import { useEffect, useMemo, useState } from "react";
import { getHealth } from "../api/reachApi";
import { useApiConfig } from "../state/ApiConfigContext";
import {
  HEARTBEAT_STORAGE_KEY,
  readHeartbeatSeconds
} from "../state/heartbeatConfig";

export function Heartbeat() {
  const { apiBase, setApiBase } = useApiConfig();
  const [isConnected, setIsConnected] = useState(false);
  const [panelOpen, setPanelOpen] = useState(false);
  const [apiInput, setApiInput] = useState(apiBase);
  const [intervalSeconds, setIntervalSeconds] = useState(() => readHeartbeatSeconds());
  const intervalMs = useMemo(() => intervalSeconds * 1000, [intervalSeconds]);

  useEffect(() => {
    setApiInput(apiBase);
  }, [apiBase]);

  useEffect(() => {
    let active = true;

    async function ping() {
      try {
        await getHealth(apiBase);
        if (active) {
          setIsConnected(true);
        }
      } catch {
        if (active) {
          setIsConnected(false);
        }
      }
    }

    ping();
    const timer = window.setInterval(ping, intervalMs);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [apiBase, intervalMs]);

  function saveSettings(event) {
    event.preventDefault();
    setApiBase(apiInput);
    try {
      window.localStorage.setItem(
        HEARTBEAT_STORAGE_KEY,
        String(Math.max(1, Math.min(120, intervalSeconds)))
      );
    } catch {
      // no-op
    }
    setPanelOpen(false);
  }

  return (
    <div className="heartbeat-wrap">
      <button
        type="button"
        className="heartbeat-button"
        aria-label="Connection settings"
        onClick={() => setPanelOpen((prev) => !prev)}
      >
        <span className={`heartbeat-light${isConnected ? " connected" : ""}`} />
      </button>

      {panelOpen && (
        <section className="heartbeat-panel">
          <h3>Connection</h3>
          <p>Status: {isConnected ? "Connected" : "Disconnected"}</p>
          <form onSubmit={saveSettings}>
            <label htmlFor="heartbeat-api-base">Admin API Endpoint</label>
            <input
              id="heartbeat-api-base"
              type="url"
              value={apiInput}
              onChange={(event) => setApiInput(event.target.value)}
              placeholder="http://127.0.0.1:8001"
              required
            />

            <label htmlFor="heartbeat-seconds">Heartbeat (seconds)</label>
            <input
              id="heartbeat-seconds"
              type="number"
              min="1"
              max="120"
              value={intervalSeconds}
              onChange={(event) => setIntervalSeconds(Number(event.target.value) || 1)}
            />

            <div className="heartbeat-actions">
              <button type="submit">Save</button>
              <button type="button" onClick={() => setPanelOpen(false)}>
                Close
              </button>
            </div>
          </form>
        </section>
      )}
    </div>
  );
}
