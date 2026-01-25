import { useEffect, useMemo, useRef, useState, useCallback, memo } from "react";

const COOKIE_KEY = "reach_admin_url";
const HEALTH_INTERVAL_MS = 10000;

function readCookie(name) {
  const match = document.cookie
    .split(";")
    .map((entry) => entry.trim())
    .find((entry) => entry.startsWith(`${name}=`));
  if (!match) {
    return "";
  }
  return decodeURIComponent(match.split("=").slice(1).join("="));
}

function writeCookie(name, value) {
  const encoded = encodeURIComponent(value.trim());
  document.cookie = `${name}=${encoded}; path=/; max-age=${60 * 60 * 24 * 365}`;
}

function formatUrl(value) {
  if (!value) {
    return "";
  }
  if (value.startsWith("http://") || value.startsWith("https://")) {
    return value.replace(/\/$/, "");
  }
  return `http://${value.replace(/\/$/, "")}`;
}

function ConnectionCard({ status, message, onChange, onRetry }) {
  return (
    <section className="card popup-card">
      <header>
        <h2>Admin API</h2>
        <p>Only connection this UI needs. Keep the UI hosted anywhere.</p>
      </header>
      <div className={`status ${status}`}>
        <span>{message}</span>
      </div>
      <div className="actions">
        <button className="btn btn-outline-secondary" type="button" onClick={onChange}>
          Change URL
        </button>
        <button className="btn btn-primary" type="button" onClick={onRetry}>
          Retest
        </button>
      </div>
    </section>
  );
}

const RouteCard = memo(function RouteCard({ route }) {
  return (
    <article className="route-card">
      <div className="route-meta">
        <span className="route-method">{route.method}</span>
        <span className="route-path">/{route.path}</span>
      </div>
      <div className="route-details">
        <span className="pill">{route.status_code}</span>
        <span className="pill">{route.content_type}</span>
        <span className="pill">encoding: {route.body_encoding}</span>
      </div>
      <p className="route-preview">
        {(route.response_body || "OK").slice(0, 120)}
        {route.response_body && route.response_body.length > 120 ? "…" : ""}
      </p>
    </article>
  );
});

function RoutesList({ routes, loading, error, onRefresh }) {
  return (
    <section className="card">
      <header className="routes-header">
        <div>
          <h2>Routes</h2>
          <p>Dynamic routes registered in the admin API.</p>
        </div>
        <button type="button" className="btn btn-outline-secondary btn-sm" onClick={onRefresh}>
          Refresh
        </button>
      </header>
      {loading ? <div className="status">Loading routes...</div> : null}
      {error ? <div className="status error">{error}</div> : null}
      {!loading && !error && routes.length === 0 ? (
        <div className="status">No routes yet.</div>
      ) : null}
      <div className="route-grid">
        {routes.map((route) => (
          <RouteCard key={route.id} route={route} />
        ))}
      </div>
    </section>
  );
}

function BuilderPlaceholder() {
  return (
    <section className="card">
      <header>
        <h2>Flow Builder</h2>
        <p>POC workspace. Next step is to drop in React Flow nodes.</p>
      </header>
      <div className="builder-grid">
        <div className="builder-panel">
          <h3>Nodes</h3>
          <ul>
            <li>Match</li>
            <li>Response</li>
            <li>Set State</li>
            <li>Forward</li>
            <li>Create Route</li>
            <li>Chain</li>
          </ul>
        </div>
        <div className="builder-panel">
          <h3>Canvas</h3>
          <div className="canvas-placeholder">Drop nodes here</div>
        </div>
        <div className="builder-panel">
          <h3>Rule JSON</h3>
          <textarea
            readOnly
            value={`{\n  "name": "example-rule",\n  "match": {},\n  "action": {}\n}`}
          />
        </div>
      </div>
    </section>
  );
}

export default function App() {
  const [storedUrl, setStoredUrl] = useState("");
  const [inputUrl, setInputUrl] = useState("");
  const [forcePrompt, setForcePrompt] = useState(false);
  const [status, setStatus] = useState("idle");
  const [message, setMessage] = useState("Provide the admin API URL to begin.");
  const intervalRef = useRef(null);
  const connectionRef = useRef("idle");
  const didFetchRoutesRef = useRef(false);
  const [routes, setRoutes] = useState([]);
  const [routesLoading, setRoutesLoading] = useState(false);
  const [routesError, setRoutesError] = useState("");

  useEffect(() => {
    const existing = readCookie(COOKIE_KEY);
    if (existing) {
      setStoredUrl(existing);
    }
  }, []);

  const normalizedUrl = useMemo(() => formatUrl(storedUrl), [storedUrl]);

  async function testConnection(url) {
    if (!url) {
      setStatus("error");
      setMessage("Missing admin URL.");
      connectionRef.current = "error";
      return;
    }
    if (connectionRef.current !== "ok") {
      setStatus("loading");
      setMessage("Connecting...");
    }
    try {
      const response = await fetch(`${url}/api/health`, {
        headers: { Accept: "application/json" }
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data = await response.json();
      setStatus("ok");
      setMessage(`Connected. Routes stored: ${data.routes ?? "n/a"}.`);
      setForcePrompt(false);
      if (connectionRef.current !== "ok") {
        didFetchRoutesRef.current = false;
      }
      connectionRef.current = "ok";
    } catch (error) {
      setStatus("error");
      setMessage(`Failed to connect: ${error.message}`);
      connectionRef.current = "error";
    }
  }

  useEffect(() => {
    if (!normalizedUrl) {
      return;
    }
    testConnection(normalizedUrl);
    intervalRef.current = setInterval(() => {
      testConnection(normalizedUrl);
    }, HEALTH_INTERVAL_MS);
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [normalizedUrl]);

  function areRoutesEqual(a, b) {
    return (
      a.id === b.id &&
      a.method === b.method &&
      a.path === b.path &&
      a.status_code === b.status_code &&
      a.response_body === b.response_body &&
      a.content_type === b.content_type &&
      a.body_encoding === b.body_encoding
    );
  }

  const fetchRoutes = useCallback(async () => {
    if (!normalizedUrl) {
      return;
    }
    setRoutesLoading(true);
    setRoutesError("");
    try {
      const response = await fetch(`${normalizedUrl}/api/routes`, {
        headers: { Accept: "application/json" }
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data = await response.json();
      setRoutes((prev) => {
        const next = Array.isArray(data) ? data : [];
        const prevById = new Map(prev.map((route) => [route.id, route]));
        return next.map((route) => {
          const existing = prevById.get(route.id);
          return existing && areRoutesEqual(existing, route) ? existing : route;
        });
      });
    } catch (error) {
      setRoutesError(`Failed to load routes: ${error.message}`);
    } finally {
      setRoutesLoading(false);
    }
  }, [normalizedUrl]);

  useEffect(() => {
    if (status === "ok" && !didFetchRoutesRef.current) {
      didFetchRoutesRef.current = true;
      fetchRoutes();
    }
  }, [status, fetchRoutes]);

  function handleSave(event) {
    event.preventDefault();
    const formatted = formatUrl(inputUrl);
    if (!formatted) {
      return;
    }
    writeCookie(COOKIE_KEY, formatted);
    setStoredUrl(formatted);
    setForcePrompt(false);
    connectionRef.current = "idle";
    didFetchRoutesRef.current = false;
    testConnection(formatted);
  }

  function handleReset() {
    setInputUrl(storedUrl);
    setForcePrompt(true);
    connectionRef.current = "idle";
    didFetchRoutesRef.current = false;
  }

  const showPrompt = forcePrompt || !normalizedUrl || status === "error";

  return (
    <div className="page">
      <header className="header">
        <div>
          <h1>REACH.UI</h1>
          <p>Admin API: {normalizedUrl || "Not configured"}</p>
        </div>
        <div className="header-actions">
          {status === "ok" ? (
            <div className="status-pill">
              <span className="pulse" />
              Connected
            </div>
          ) : null}
          <button className="btn btn-outline-secondary" type="button" onClick={handleReset}>
            Edit URL
          </button>
        </div>
      </header>
      <div className="grid">
        <RoutesList
          routes={routes}
          loading={routesLoading}
          error={routesError}
          onRefresh={fetchRoutes}
        />
        <BuilderPlaceholder />
      </div>
      {status === "error" ? (
        <ConnectionCard
          status={status}
          message={message}
          onChange={handleReset}
          onRetry={() => testConnection(normalizedUrl)}
        />
      ) : null}
      {showPrompt ? (
        <div className="modal-backdrop">
          <main className="card hero modal">
            <h1>Connect to REACH Admin</h1>
            <p>
              Enter the admin API base URL. It will be stored in a cookie so future sessions can load your rules
              quickly.
            </p>
            <form onSubmit={handleSave}>
              <label htmlFor="admin-url">Admin URL</label>
              <input
                id="admin-url"
                type="text"
                placeholder="http://127.0.0.1:8001"
                value={inputUrl}
                onChange={(event) => setInputUrl(event.target.value)}
                className="form-control"
                required
              />
              <button className="btn btn-primary" type="submit">
                Save & Continue
              </button>
            </form>
            <p className="hint">CORS must allow this UI origin.</p>
          </main>
        </div>
      ) : null}
    </div>
  );
}
