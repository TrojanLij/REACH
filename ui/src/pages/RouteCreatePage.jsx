import { useMemo, useState } from "react";
import { createRoute } from "../api/reachApi";
import { useApiConfig } from "../state/ApiConfigContext";

function parseHeaders(rawValue) {
  const value = rawValue.trim();
  if (!value) {
    return {};
  }
  const parsed = JSON.parse(value);
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new Error("Headers must be a JSON object.");
  }
  return parsed;
}

export function RouteCreatePage() {
  const { apiBase } = useApiConfig();
  const [method, setMethod] = useState("GET");
  const [path, setPath] = useState("/demo");
  const [statusCode, setStatusCode] = useState(200);
  const [contentType, setContentType] = useState("text/plain");
  const [responseBody, setResponseBody] = useState("hello from REACH UI");
  const [headersRaw, setHeadersRaw] = useState("{}");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [createdRoute, setCreatedRoute] = useState(null);

  const normalizedPath = useMemo(() => path.trim().replace(/^\/+/, ""), [path]);

  async function onSubmit(event) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setCreatedRoute(null);

    try {
      const headers = parseHeaders(headersRaw);
      const payload = {
        method: method.toUpperCase(),
        path: normalizedPath,
        status_code: Number(statusCode),
        response_body: responseBody,
        content_type: contentType,
        headers
      };
      const result = await createRoute(payload, apiBase);
      setCreatedRoute(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create route.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <section>
      <h2>Add Route</h2>
      <p>Create a new dynamic route from the UI.</p>

      <form className="route-form" onSubmit={onSubmit}>
        <label htmlFor="route-method">Method</label>
        <select
          id="route-method"
          value={method}
          onChange={(event) => setMethod(event.target.value)}
        >
          <option value="GET">GET</option>
          <option value="POST">POST</option>
          <option value="PUT">PUT</option>
          <option value="PATCH">PATCH</option>
          <option value="DELETE">DELETE</option>
        </select>

        <label htmlFor="route-path">Path</label>
        <input
          id="route-path"
          type="text"
          value={path}
          onChange={(event) => setPath(event.target.value)}
          placeholder="/example"
          required
        />

        <label htmlFor="route-status">Status Code</label>
        <input
          id="route-status"
          type="number"
          min="100"
          max="599"
          value={statusCode}
          onChange={(event) => setStatusCode(event.target.value)}
          required
        />

        <label htmlFor="route-content-type">Content Type</label>
        <input
          id="route-content-type"
          type="text"
          value={contentType}
          onChange={(event) => setContentType(event.target.value)}
          required
        />

        <label htmlFor="route-response-body">Response Body</label>
        <textarea
          id="route-response-body"
          value={responseBody}
          onChange={(event) => setResponseBody(event.target.value)}
          rows={5}
        />

        <label htmlFor="route-headers">Headers (JSON)</label>
        <textarea
          id="route-headers"
          value={headersRaw}
          onChange={(event) => setHeadersRaw(event.target.value)}
          rows={4}
          placeholder='{"X-Source":"reach-ui"}'
        />

        <button type="submit" disabled={saving}>
          {saving ? "Saving..." : "Create Route"}
        </button>
      </form>

      {error && <p className="error">{error}</p>}
      {createdRoute && (
        <section className="panel">
          <h3>Created Route</h3>
          <pre>{JSON.stringify(createdRoute, null, 2)}</pre>
        </section>
      )}
    </section>
  );
}
