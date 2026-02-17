import { useEffect, useState } from "react";
import { deleteRoute, listRoutes, updateRoute } from "../api/reachApi";
import { useApiConfig } from "../state/ApiConfigContext";

function normalizeRoutes(data) {
  if (Array.isArray(data)) {
    return data;
  }
  if (data && Array.isArray(data.items)) {
    return data.items;
  }
  return [];
}

export function RoutesListPage() {
  const { apiBase } = useApiConfig();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [routes, setRoutes] = useState(null);
  const [deletingRouteId, setDeletingRouteId] = useState(null);
  const [editingRouteId, setEditingRouteId] = useState(null);
  const [savingRouteId, setSavingRouteId] = useState(null);
  const [editForm, setEditForm] = useState({
    method: "GET",
    path: "",
    status_code: 200,
    content_type: "text/plain",
    body_encoding: "none",
    response_body: "",
    headers: "{}"
  });

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError("");
      try {
        const data = await listRoutes(apiBase);
        setRoutes(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load routes.");
      } finally {
        setLoading(false);
      }
    }

    load();
  }, [apiBase]);

  async function onDeleteRoute(route) {
    if (!route?.id) {
      return;
    }
    const confirmed = window.confirm(
      `Delete route ${route.method} /${route.path}? This cannot be undone.`
    );
    if (!confirmed) {
      return;
    }

    setDeletingRouteId(route.id);
    setError("");
    try {
      await deleteRoute(route.id, apiBase);
      setRoutes((prev) => normalizeRoutes(prev).filter((r) => r.id !== route.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete route.");
    } finally {
      setDeletingRouteId(null);
    }
  }

  function startEditRoute(route) {
    setError("");
    setEditingRouteId(route.id ?? null);
    setEditForm({
      method: route.method || "GET",
      path: `/${route.path || ""}`,
      status_code: route.status_code ?? 200,
      content_type: route.content_type || "text/plain",
      body_encoding: route.body_encoding || "none",
      response_body: route.response_body || "",
      headers: JSON.stringify(route.headers || {}, null, 2)
    });
  }

  function cancelEditRoute() {
    setEditingRouteId(null);
    setSavingRouteId(null);
  }

  async function saveEditRoute(route) {
    if (!route?.id) {
      return;
    }
    setError("");
    setSavingRouteId(route.id);

    try {
      let parsedHeaders = {};
      const rawHeaders = editForm.headers.trim();
      if (rawHeaders) {
        parsedHeaders = JSON.parse(rawHeaders);
        if (
          !parsedHeaders ||
          typeof parsedHeaders !== "object" ||
          Array.isArray(parsedHeaders)
        ) {
          throw new Error("Headers must be a JSON object.");
        }
      }

      const payload = {
        method: String(editForm.method || "GET").toUpperCase(),
        path: String(editForm.path || "").trim().replace(/^\/+/, ""),
        status_code: Number(editForm.status_code),
        content_type: String(editForm.content_type || "text/plain"),
        body_encoding: String(editForm.body_encoding || "none"),
        response_body: String(editForm.response_body || ""),
        headers: parsedHeaders
      };

      const updated = await updateRoute(route.id, payload, apiBase);
      setRoutes((prev) =>
        normalizeRoutes(prev).map((current) =>
          current.id === route.id ? updated : current
        )
      );
      setEditingRouteId(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update route.");
    } finally {
      setSavingRouteId(null);
    }
  }

  return (
    <section>
      <h2>Routes</h2>
      <p>View currently registered dynamic routes.</p>
      {loading && <p>Loading routes...</p>}
      {error && <p className="error">{error}</p>}
      {routes && (
        <div className="routes-list">
          {normalizeRoutes(routes).length === 0 && (
            <p>No dynamic routes found.</p>
          )}
          {normalizeRoutes(routes).map((route) => (
            <details
              key={`${route.id ?? "route"}-${route.method}-${route.path}`}
              className="route-item"
            >
              <summary>
                <span className="route-slash">/</span>
                <span>{route.path || ""}</span>
                <span className="route-summary-method">[{route.method}]</span>
                <span className="route-summary-status">- {route.status_code}</span>
              </summary>
              <div className="route-item-details">
                {editingRouteId === route.id ? (
                  <div className="route-edit-form">
                    <label>
                      Method
                      <select
                        value={editForm.method}
                        onChange={(event) =>
                          setEditForm((prev) => ({
                            ...prev,
                            method: event.target.value
                          }))
                        }
                      >
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
                        value={editForm.path}
                        onChange={(event) =>
                          setEditForm((prev) => ({ ...prev, path: event.target.value }))
                        }
                      />
                    </label>
                    <label>
                      Status Code
                      <input
                        type="number"
                        min="100"
                        max="599"
                        value={editForm.status_code}
                        onChange={(event) =>
                          setEditForm((prev) => ({
                            ...prev,
                            status_code: event.target.value
                          }))
                        }
                      />
                    </label>
                    <label>
                      Content Type
                      <input
                        type="text"
                        value={editForm.content_type}
                        onChange={(event) =>
                          setEditForm((prev) => ({
                            ...prev,
                            content_type: event.target.value
                          }))
                        }
                      />
                    </label>
                    <label>
                      Body Encoding
                      <select
                        value={editForm.body_encoding}
                        onChange={(event) =>
                          setEditForm((prev) => ({
                            ...prev,
                            body_encoding: event.target.value
                          }))
                        }
                      >
                        <option value="none">none</option>
                        <option value="base64">base64</option>
                      </select>
                    </label>
                    <label>
                      Response Body
                      <textarea
                        rows={4}
                        value={editForm.response_body}
                        onChange={(event) =>
                          setEditForm((prev) => ({
                            ...prev,
                            response_body: event.target.value
                          }))
                        }
                      />
                    </label>
                    <label>
                      Headers (JSON)
                      <textarea
                        rows={4}
                        value={editForm.headers}
                        onChange={(event) =>
                          setEditForm((prev) => ({ ...prev, headers: event.target.value }))
                        }
                      />
                    </label>
                    <div className="route-actions">
                      <button
                        type="button"
                        className="route-save-btn"
                        disabled={savingRouteId === route.id}
                        onClick={() => saveEditRoute(route)}
                      >
                        {savingRouteId === route.id ? "Saving..." : "Save Changes"}
                      </button>
                      <button
                        type="button"
                        className="route-cancel-btn"
                        disabled={savingRouteId === route.id}
                        onClick={cancelEditRoute}
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <>
                    <p>
                      <strong>ID:</strong> {route.id ?? "n/a"}
                    </p>
                    <p>
                      <strong>Content Type:</strong> {route.content_type || "n/a"}
                    </p>
                    <p>
                      <strong>Body Encoding:</strong> {route.body_encoding || "none"}
                    </p>
                    <p>
                      <strong>Headers:</strong>
                    </p>
                    <pre>{JSON.stringify(route.headers || {}, null, 2)}</pre>
                    <p>
                      <strong>Response Body:</strong>
                    </p>
                    <pre>{route.response_body || ""}</pre>
                    <div className="route-actions">
                      <button
                        type="button"
                        className="route-edit-btn"
                        disabled={!route.id || deletingRouteId === route.id}
                        onClick={() => startEditRoute(route)}
                      >
                        Edit Route
                      </button>
                      <button
                        type="button"
                        className="route-delete-btn"
                        disabled={!route.id || deletingRouteId === route.id}
                        onClick={() => onDeleteRoute(route)}
                      >
                        {deletingRouteId === route.id ? "Deleting..." : "Delete Route"}
                      </button>
                    </div>
                  </>
                )}
              </div>
            </details>
          ))}
        </div>
      )}
    </section>
  );
}
