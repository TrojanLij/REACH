import { useMemo, useRef, useState } from "react";
import { fetchLogs } from "../api/reachApi";
import { useApiConfig } from "../state/ApiConfigContext";

const PLAYGROUND_PUBLIC_BASE_KEY = "reach_playground_public_base";

function inferPublicBase(apiBase) {
  try {
    const url = new URL(apiBase);
    if (url.port === "8001") {
      url.port = "8000";
    }
    return `${url.protocol}//${url.host}`;
  } catch {
    return "http://127.0.0.1:8000";
  }
}

function readStoredPublicBase(fallback) {
  try {
    return window.localStorage.getItem(PLAYGROUND_PUBLIC_BASE_KEY) || fallback;
  } catch {
    return fallback;
  }
}

function parseJsonObject(raw, label) {
  const value = raw.trim();
  if (!value) {
    return {};
  }
  const parsed = JSON.parse(value);
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new Error(`${label} must be a JSON object.`);
  }
  return parsed;
}

function buildQueryString(queryObject) {
  const params = new URLSearchParams();
  Object.entries(queryObject).forEach(([key, value]) => {
    params.set(String(key), String(value));
  });
  const query = params.toString();
  return query ? `?${query}` : "";
}

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

export function PlaygroundPage() {
  const { apiBase } = useApiConfig();
  const defaultPublicBase = useMemo(() => inferPublicBase(apiBase), [apiBase]);
  const [publicBase, setPublicBase] = useState(() => readStoredPublicBase(defaultPublicBase));
  const [method, setMethod] = useState("GET");
  const [path, setPath] = useState("/demo");
  const [queryRaw, setQueryRaw] = useState("{}");
  const [headersRaw, setHeadersRaw] = useState("{}");
  const [body, setBody] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [responseData, setResponseData] = useState(null);
  const [matchedLogs, setMatchedLogs] = useState([]);
  const lastSeenLogIdRef = useRef(0);

  function persistPublicBase(nextValue) {
    setPublicBase(nextValue);
    try {
      window.localStorage.setItem(PLAYGROUND_PUBLIC_BASE_KEY, nextValue);
    } catch {
      // no-op
    }
  }

  async function runSimulation(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setMatchedLogs([]);

    try {
      const queryObj = parseJsonObject(queryRaw, "Query");
      const headersObj = parseJsonObject(headersRaw, "Headers");
      const normalizedPath = `/${String(path || "").replace(/^\/+/, "")}`;
      const url = `${publicBase.replace(/\/$/, "")}${normalizedPath}${buildQueryString(queryObj)}`;
      const requestStartMs = Date.now();

      const response = await fetch(url, {
        method,
        headers: headersObj,
        body: method === "GET" || method === "DELETE" ? undefined : body
      });

      const responseText = await response.text();
      const responseHeaders = Object.fromEntries(response.headers.entries());
      const elapsedMs = Date.now() - requestStartMs;

      setResponseData({
        url,
        status: response.status,
        ok: response.ok,
        elapsedMs,
        headers: responseHeaders,
        body: responseText
      });

      // Pull recent logs after request and filter by exact method+path.
      const logs = await fetchLogs({
        sinceId: lastSeenLogIdRef.current,
        limit: 200,
        apiBase
      });
      if (logs.length > 0) {
        lastSeenLogIdRef.current = logs[logs.length - 1].id;
      }
      const relevant = logs.filter(
        (entry) =>
          String(entry.method || "").toUpperCase() === method &&
          String(entry.path || "") === normalizedPath
      );
      setMatchedLogs(relevant);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Simulation failed.");
      setResponseData(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section>
      <h2>Playground</h2>
      <p>Simulate requests against public routes and inspect response + matching logs.</p>

      <form className="playground-form" onSubmit={runSimulation}>
        <label>
          Public Base URL
          <input
            type="url"
            value={publicBase}
            onChange={(event) => persistPublicBase(event.target.value)}
            placeholder="http://127.0.0.1:8000"
            required
          />
        </label>

        <label>
          Method
          <select value={method} onChange={(event) => setMethod(event.target.value)}>
            <option value="GET">GET</option>
            <option value="POST">POST</option>
            <option value="PUT">PUT</option>
            <option value="PATCH">PATCH</option>
            <option value="DELETE">DELETE</option>
          </select>
        </label>

        <label>
          Path
          <input
            type="text"
            value={path}
            onChange={(event) => setPath(event.target.value)}
            placeholder="/demo"
            required
          />
        </label>

        <label>
          Query JSON
          <textarea
            rows={3}
            value={queryRaw}
            onChange={(event) => setQueryRaw(event.target.value)}
            placeholder='{"token":"abc"}'
          />
        </label>

        <label>
          Headers JSON
          <textarea
            rows={3}
            value={headersRaw}
            onChange={(event) => setHeadersRaw(event.target.value)}
            placeholder='{"Content-Type":"text/plain"}'
          />
        </label>

        <label>
          Body
          <textarea
            rows={5}
            value={body}
            onChange={(event) => setBody(event.target.value)}
            placeholder="Request body for POST/PUT/PATCH"
          />
        </label>

        <button type="submit" disabled={loading}>
          {loading ? "Running..." : "Run Simulation"}
        </button>
      </form>

      {error && <p className="error">{error}</p>}

      {responseData && (
        <section className="playground-panel">
          <h3>Response</h3>
          <p>
            <strong>Status:</strong> {responseData.status} | <strong>OK:</strong>{" "}
            {String(responseData.ok)} | <strong>Duration:</strong> {responseData.elapsedMs}ms
          </p>
          <p>
            <strong>URL:</strong> {responseData.url}
          </p>
          <p>
            <strong>Headers:</strong>
          </p>
          <pre>{JSON.stringify(responseData.headers, null, 2)}</pre>
          <p>
            <strong>Body:</strong>
          </p>
          <pre>{responseData.body}</pre>
        </section>
      )}

      <section className="playground-panel">
        <h3>Matching Logs</h3>
        {matchedLogs.length === 0 ? (
          <p>No matching logs captured for the last simulation request.</p>
        ) : (
          <div className="playground-log-list">
            {matchedLogs.map((entry) => (
              <details key={entry.id} className="playground-log-item">
                <summary>
                  [{formatTimestampUtc(entry.timestamp)}] {entry.method} {entry.path} -{" "}
                  {entry.status_code ?? "-"}
                </summary>
                <div>
                  <p>
                    <strong>ID:</strong> {entry.id} | <strong>Protocol:</strong>{" "}
                    {entry.protocol}
                  </p>
                  <p>
                    <strong>Client IP:</strong> {entry.client_ip || "-"} |{" "}
                    <strong>Host:</strong> {entry.host || "-"}
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
                </div>
              </details>
            ))}
          </div>
        )}
      </section>
    </section>
  );
}
