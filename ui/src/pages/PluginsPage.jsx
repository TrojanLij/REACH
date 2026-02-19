import { useEffect, useMemo, useState } from "react";
import {
  getIftttFilterSource,
  listIftttFilters,
  testIftttFilterExpression
} from "../api/reachApi";
import { useApiConfig } from "../state/ApiConfigContext";

export function PluginsPage() {
  const { apiBase } = useApiConfig();
  const [activeCategory, setActiveCategory] = useState("ifttt");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filters, setFilters] = useState([]);
  const [selectedFilterName, setSelectedFilterName] = useState("");
  const [sourceLoading, setSourceLoading] = useState(false);
  const [sourceError, setSourceError] = useState("");
  const [selectedSource, setSelectedSource] = useState(null);
  const [testContextDraft, setTestContextDraft] = useState(
    '{\n  "body": "{\\"a\\":1,\\"nested\\":{\\"value\\":42}}",\n  "headers": {\n    "cookie": "sid=abc123; theme=dark"\n  },\n  "query": {\n    "id": "7"\n  }\n}'
  );
  const [testExpressionDraft, setTestExpressionDraft] = useState(
    "body|json_unwrap|json_get:nested.value"
  );
  const [testRunning, setTestRunning] = useState(false);
  const [testError, setTestError] = useState("");
  const [testResult, setTestResult] = useState(null);

  const sortedFilters = useMemo(
    () => [...filters].sort((a, b) => String(a.name).localeCompare(String(b.name))),
    [filters]
  );

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError("");
      try {
        const data = await listIftttFilters(apiBase);
        const nextFilters = Array.isArray(data) ? data : [];
        setFilters(nextFilters);
        if (nextFilters.length > 0) {
          setSelectedFilterName((prev) => prev || String(nextFilters[0].name || ""));
        } else {
          setSelectedFilterName("");
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load filter plugins.");
        setFilters([]);
        setSelectedFilterName("");
      } finally {
        setLoading(false);
      }
    }

    load();
  }, [apiBase]);

  useEffect(() => {
    if (!selectedFilterName || activeCategory !== "ifttt") {
      setSelectedSource(null);
      setSourceError("");
      return;
    }

    async function loadSource() {
      setSourceLoading(true);
      setSourceError("");
      try {
        const data = await getIftttFilterSource(selectedFilterName, apiBase);
        setSelectedSource(data);
      } catch (err) {
        setSelectedSource(null);
        setSourceError(err instanceof Error ? err.message : "Failed to load filter source.");
      } finally {
        setSourceLoading(false);
      }
    }

    loadSource();
  }, [selectedFilterName, activeCategory, apiBase]);

  async function onRunFilterTest() {
    setTestError("");
    setTestResult(null);
    setTestRunning(true);
    try {
      const parsed = JSON.parse(testContextDraft);
      if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
        throw new Error("Mock context must be a JSON object.");
      }
      const data = await testIftttFilterExpression(testExpressionDraft, parsed, apiBase);
      setTestResult(data);
    } catch (err) {
      setTestError(err instanceof Error ? err.message : "Failed to run filter test.");
    } finally {
      setTestRunning(false);
    }
  }

  return (
    <section>
      <h2>Plugin Studio</h2>
      <p>Browse plugin categories and manage plugin assets.</p>

      <div className="plugin-categories">
        <button
          type="button"
          className={activeCategory === "ifttt" ? "active" : ""}
          onClick={() => setActiveCategory("ifttt")}
        >
          IFTTT Filters
        </button>
        <button
          type="button"
          className={activeCategory === "forge" ? "active" : ""}
          onClick={() => setActiveCategory("forge")}
        >
          Forge Plugins
        </button>
      </div>

      {activeCategory === "ifttt" ? (
        <section className="plugin-panel">
          <h3>IFTTT Filters</h3>
          <p>Loaded filters available for rule template pipelines.</p>
          {loading && <p>Loading filters...</p>}
          {error && <p className="error">{error}</p>}
          {!loading && !error && sortedFilters.length === 0 && <p>No filters found.</p>}
          {!loading && !error && sortedFilters.length > 0 && (
            <div className="plugin-filter-workspace">
              <div className="plugin-filter-list">
                {sortedFilters.map((item) => (
                  <article
                    key={item.name}
                    className={`plugin-filter-item${selectedFilterName === item.name ? " active" : ""}`}
                  >
                    <button
                      type="button"
                      className="plugin-filter-select"
                      onClick={() => setSelectedFilterName(item.name)}
                    >
                      <h4>{item.name}</h4>
                    </button>
                    <p>
                      <strong>Source:</strong> {item.source}
                    </p>
                    <p>
                      <strong>Module:</strong> {item.module}
                    </p>
                    <p>
                      <strong>File:</strong> {item.file || "n/a"}
                    </p>
                  </article>
                ))}
              </div>

              <div className="plugin-code-panel">
                <h4>
                  Python Editor: {selectedFilterName || "No filter selected"}
                </h4>
                {sourceLoading && <p>Loading source...</p>}
                {sourceError && <p className="error">{sourceError}</p>}
                {!sourceLoading && !sourceError && selectedSource && (
                  <>
                    <p>
                      <strong>File:</strong> {selectedSource.file}
                    </p>
                    <textarea
                      className="plugin-code-editor"
                      value={selectedSource.code || ""}
                      readOnly
                      spellCheck={false}
                    />
                  </>
                )}
              </div>
            </div>
          )}

          {!loading && !error && (
            <div className="plugin-test-panel">
              <h4>Filter Tester</h4>
              <p>Run template/filter expressions against mock context data.</p>
              <label>
                Mock Context JSON
                <textarea
                  className="plugin-test-input"
                  value={testContextDraft}
                  onChange={(event) => setTestContextDraft(event.target.value)}
                  spellCheck={false}
                />
              </label>
              <label>
                Query / Expression
                <textarea
                  className="plugin-test-expression"
                  value={testExpressionDraft}
                  onChange={(event) => setTestExpressionDraft(event.target.value)}
                  spellCheck={false}
                />
              </label>
              <div className="plugin-test-actions">
                <button type="button" onClick={onRunFilterTest} disabled={testRunning}>
                  {testRunning ? "Running..." : "Run Expression"}
                </button>
              </div>
              {testError && <p className="error">{testError}</p>}
              {testResult && (
                <div className="plugin-test-output">
                  <p>
                    <strong>Template:</strong> {testResult.template}
                  </p>
                  <p>
                    <strong>Result:</strong>
                  </p>
                  <pre>{String(testResult.result ?? "")}</pre>
                </div>
              )}
            </div>
          )}
        </section>
      ) : (
        <section className="plugin-panel">
          <h3>Forge Plugins</h3>
          <p>Forge plugin listing/editor is the next step.</p>
        </section>
      )}
    </section>
  );
}
