import { useEffect, useMemo, useRef, useState } from "react";
import { fetchLogs } from "../api/reachApi";
import { useApiConfig } from "../state/ApiConfigContext";
import { readHeartbeatSeconds } from "../state/heartbeatConfig";

function formatTimestampUtc(timestamp) {
  if (!timestamp) {
    return "---- -- -- --:--:-- UTC";
  }
  const parsed = new Date(timestamp);
  if (Number.isNaN(parsed.getTime())) {
    return String(timestamp);
  }
  const year = parsed.getUTCFullYear();
  const month = String(parsed.getUTCMonth() + 1).padStart(2, "0");
  const day = String(parsed.getUTCDate()).padStart(2, "0");
  const hour = String(parsed.getUTCHours()).padStart(2, "0");
  const minute = String(parsed.getUTCMinutes()).padStart(2, "0");
  const second = String(parsed.getUTCSeconds()).padStart(2, "0");
  return `${year}-${month}-${day} ${hour}:${minute}:${second} UTC`;
}

function formatQuery(queryParams) {
  const pairs = Object.entries(queryParams || {});
  if (pairs.length === 0) {
    return "";
  }
  return pairs
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
    .join("&");
}

function formatEntry(entry) {
  const ts = formatTimestampUtc(entry.timestamp);
  const method = entry.method || "UNK";
  const status = entry.status_code ?? "-";
  const protocol = entry.protocol || "http";
  return `[${ts}] [${protocol}] ${method} ${entry.path} -> ${status}`;
}

export function LogsConsolePage() {
  const { apiBase } = useApiConfig();
  const [entries, setEntries] = useState([]);
  const [error, setError] = useState("");
  const [pollSeconds, setPollSeconds] = useState(() => readHeartbeatSeconds());
  const [limit, setLimit] = useState(100);
  const [protocol, setProtocol] = useState("");
  const [paused, setPaused] = useState(false);
  const [loading, setLoading] = useState(true);
  const [autoScroll, setAutoScroll] = useState(true);
  const sinceIdRef = useRef(0);
  const viewportRef = useRef(null);
  const pollMs = useMemo(() => Math.max(1, pollSeconds) * 1000, [pollSeconds]);

  useEffect(() => {
    setEntries([]);
    sinceIdRef.current = 0;
  }, [apiBase, protocol]);

  useEffect(() => {
    let active = true;

    async function loadLogs() {
      if (paused) {
        return;
      }
      try {
        const data = await fetchLogs({
          sinceId: sinceIdRef.current,
          limit,
          protocol,
          apiBase
        });
        if (!active) {
          return;
        }
        if (data.length > 0) {
          setEntries((prev) => {
            const merged = [...prev, ...data];
            return merged.slice(-500);
          });
          sinceIdRef.current = data[data.length - 1].id;
        }
        setError("");
      } catch (err) {
        if (active) {
          setError(err instanceof Error ? err.message : "Failed to fetch logs.");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    loadLogs();
    const timer = window.setInterval(loadLogs, pollMs);

    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [apiBase, limit, paused, pollMs, protocol]);

  useEffect(() => {
    if (!autoScroll || !viewportRef.current) {
      return;
    }
    viewportRef.current.scrollTop = viewportRef.current.scrollHeight;
  }, [entries, autoScroll]);

  return (
    <section>
      <h2>Logs Console</h2>
      <p>Live request log stream from the admin API.</p>

      <div className="logs-toolbar">
        <label>
          Poll (sec)
          <input
            type="number"
            min="1"
            max="30"
            value={pollSeconds}
            onChange={(event) => setPollSeconds(Number(event.target.value) || 1)}
          />
        </label>

        <label>
          Batch Limit
          <input
            type="number"
            min="1"
            max="500"
            value={limit}
            onChange={(event) => setLimit(Number(event.target.value) || 100)}
          />
        </label>

        <label>
          Protocol
          <select
            value={protocol}
            onChange={(event) => setProtocol(event.target.value)}
          >
            <option value="">all</option>
            <option value="http">http</option>
            <option value="dns">dns</option>
            <option value="ftp">ftp</option>
            <option value="wss">wss</option>
          </select>
        </label>

        <button type="button" onClick={() => setPaused((prev) => !prev)}>
          {paused ? "Resume" : "Pause"}
        </button>
        <button
          type="button"
          onClick={() => {
            setEntries([]);
            sinceIdRef.current = 0;
          }}
        >
          Clear
        </button>
        <button type="button" onClick={() => setAutoScroll((prev) => !prev)}>
          {autoScroll ? "Auto-scroll On" : "Auto-scroll Off"}
        </button>
      </div>

      {loading && <p>Loading logs...</p>}
      {error && <p className="error">{error}</p>}

      <div className="logs-console" ref={viewportRef}>
        {entries.length === 0 && !loading && <p className="logs-empty">No logs yet.</p>}
        {entries.map((entry) => (
          <details key={entry.id} className="log-line">
            <summary>
              <div className="log-main">{formatEntry(entry)}</div>
              <div className="log-meta">
                id={entry.id} | ip={entry.client_ip || "-"}
                {entry.host ? ` | host=${entry.host}` : ""}
                {entry.route_id ? ` | route=${entry.route_id}` : ""}
              </div>
            </summary>
            <div className="log-details">
              <p>
                <strong>Path:</strong> {entry.path}
                {formatQuery(entry.query_params) ? `?${formatQuery(entry.query_params)}` : ""}
              </p>
              <p>
                <strong>Method:</strong> {entry.method} | <strong>Status:</strong>{" "}
                {entry.status_code ?? "-"} | <strong>Protocol:</strong> {entry.protocol}
              </p>
              <p>
                <strong>Timestamp:</strong> {formatTimestampUtc(entry.timestamp)}
              </p>
              <p>
                <strong>Headers:</strong>
              </p>
              <pre>{JSON.stringify(entry.headers || {}, null, 2)}</pre>
              <p>
                <strong>Query Params:</strong>
              </p>
              <pre>{JSON.stringify(entry.query_params || {}, null, 2)}</pre>
              <p>
                <strong>Body:</strong>
              </p>
              <pre>{entry.body || ""}</pre>
              {entry.raw_bytes && (
                <>
                  <p>
                    <strong>Raw Bytes ({entry.raw_bytes_encoding || "none"}):</strong>
                  </p>
                  <pre>{entry.raw_bytes}</pre>
                </>
              )}
            </div>
          </details>
        ))}
      </div>
    </section>
  );
}
