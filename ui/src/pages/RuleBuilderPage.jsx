import { useEffect, useMemo, useState } from "react";
import {
  Background,
  Controls,
  MarkerType,
  // MiniMap,
  ReactFlow,
  useEdgesState,
  useNodesState
} from "@xyflow/react";
import {
  createRule,
  deleteRule,
  listRuleFilters,
  listRules,
  previewRule,
  updateRule
} from "../api/reachApi";
import { useApiConfig } from "../state/ApiConfigContext";
import {
  defaultRuleForm,
  formToGraphNodes,
  formToRulePayload,
  graphToJson,
  jsonToGraph,
  rulePayloadToForm
} from "../features/rules/ruleMapper";

const BASE_NODES = [
  {
    id: "meta",
    position: { x: 60, y: 120 },
    data: { label: "Rule Meta" },
    style: { width: 220 }
  },
  {
    id: "match",
    position: { x: 360, y: 60 },
    data: { label: "When / Match" },
    style: { width: 280 }
  },
  {
    id: "action",
    position: { x: 360, y: 230 },
    data: { label: "Then / Action" },
    style: { width: 280 }
  }
];

const BASE_EDGES = [
  {
    id: "edge-meta-match",
    source: "meta",
    target: "match",
    markerEnd: { type: MarkerType.ArrowClosed }
  },
  {
    id: "edge-match-action",
    source: "match",
    target: "action",
    markerEnd: { type: MarkerType.ArrowClosed }
  }
];

export function RuleBuilderPage() {
  const { apiBase } = useApiConfig();
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [selectedRuleId, setSelectedRuleId] = useState(null);
  const [selectedNodeId, setSelectedNodeId] = useState("match");
  const [editorTab, setEditorTab] = useState("diagram");
  const [jsonDraft, setJsonDraft] = useState("");
  const [jsonError, setJsonError] = useState("");
  const [form, setForm] = useState(defaultRuleForm);
  const [testMethod, setTestMethod] = useState("GET");
  const [testPath, setTestPath] = useState("/demo");
  const [testHost, setTestHost] = useState("localhost");
  const [testClientIp, setTestClientIp] = useState("127.0.0.1");
  const [testBody, setTestBody] = useState("");
  const [testHeadersJson, setTestHeadersJson] = useState("{}");
  const [testQueryJson, setTestQueryJson] = useState("{}");
  const [testRouteExists, setTestRouteExists] = useState(true);
  const [testStateKey, setTestStateKey] = useState("");
  const [testStateJson, setTestStateJson] = useState("{}");
  const [testError, setTestError] = useState("");
  const [testTrace, setTestTrace] = useState(null);
  const [availableFilters, setAvailableFilters] = useState([]);
  const [nodes, setNodes, onNodesChange] = useNodesState(
    formToGraphNodes(defaultRuleForm(), BASE_NODES)
  );
  const [edges, setEdges, onEdgesChange] = useEdgesState(BASE_EDGES);

  useEffect(() => {
    async function loadRules() {
      setLoading(true);
      setError("");
      try {
        const data = await listRules(apiBase);
        setRules(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load rules.");
      } finally {
        setLoading(false);
      }
    }
    loadRules();
  }, [apiBase]);

  useEffect(() => {
    async function loadFilters() {
      try {
        const filters = await listRuleFilters(apiBase);
        setAvailableFilters(Array.isArray(filters) ? filters : []);
      } catch {
        setAvailableFilters([]);
      }
    }
    loadFilters();
  }, [apiBase]);

  useEffect(() => {
    const updatedNodes = formToGraphNodes(form, BASE_NODES).map((templateNode) => {
      const existing = nodes.find((n) => n.id === templateNode.id);
      if (!existing) {
        return templateNode;
      }
      return {
        ...existing,
        data: templateNode.data
      };
    });
    setNodes(updatedNodes);
    if (editorTab !== "json") {
      setJsonDraft(graphToJson({ form }).json);
      setJsonError("");
    }
  }, [form, setNodes, editorTab]);

  const preview = useMemo(() => graphToJson({ form }), [form]);

  function parseJsonObject(raw, label) {
    const value = String(raw || "").trim();
    if (!value) {
      return {};
    }
    const parsed = JSON.parse(value);
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
      throw new Error(`${label} must be a JSON object.`);
    }
    return parsed;
  }

  async function onSaveRule() {
    setSaving(true);
    setError("");
    setJsonError("");
    try {
      let payload;
      if (editorTab === "json") {
        const parsed = JSON.parse(jsonDraft);
        const mapped = jsonToGraph(parsed, BASE_NODES);
        setForm(mapped.form);
        payload = parsed;
      } else {
        payload = formToRulePayload(form, { strict: true }).payload;
      }

      let saved;
      if (selectedRuleId) {
        saved = await updateRule(selectedRuleId, payload, apiBase);
        setRules((prev) => prev.map((rule) => (rule.id === selectedRuleId ? saved : rule)));
      } else {
        saved = await createRule(payload, apiBase);
        setRules((prev) => [...prev, saved]);
        setSelectedRuleId(saved.id);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to save rule.";
      if (editorTab === "json") {
        setJsonError(message);
      } else {
        setError(message);
      }
    } finally {
      setSaving(false);
    }
  }

  async function onDeleteRule() {
    if (!selectedRuleId) {
      return;
    }
    const confirmed = window.confirm("Delete selected rule?");
    if (!confirmed) {
      return;
    }
    setSaving(true);
    setError("");
    try {
      await deleteRule(selectedRuleId, apiBase);
      setRules((prev) => prev.filter((rule) => rule.id !== selectedRuleId));
      setSelectedRuleId(null);
      const resetForm = defaultRuleForm();
      setForm(resetForm);
      setNodes(formToGraphNodes(resetForm, BASE_NODES));
      setEdges(BASE_EDGES);
      setJsonDraft(graphToJson({ form: resetForm }).json);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete rule.");
    } finally {
      setSaving(false);
    }
  }

  function onSelectRule(rule) {
    setSelectedRuleId(rule.id);
    const nextForm = rulePayloadToForm(rule);
    setForm(nextForm);
    setNodes(formToGraphNodes(nextForm, BASE_NODES));
    setEdges(BASE_EDGES);
    setJsonDraft(JSON.stringify(rule, null, 2));
    setJsonError("");
  }

  function onNewRule() {
    setSelectedRuleId(null);
    const nextForm = defaultRuleForm();
    setForm(nextForm);
    setSelectedNodeId("match");
    setNodes(formToGraphNodes(nextForm, BASE_NODES));
    setEdges(BASE_EDGES);
    setJsonDraft(graphToJson({ form: nextForm }).json);
    setJsonError("");
  }

  function onApplyJson() {
    setJsonError("");
    try {
      const mapped = jsonToGraph(jsonDraft, BASE_NODES);
      setForm(mapped.form);
      setNodes(mapped.nodes);
      setEdges(BASE_EDGES);
    } catch (err) {
      setJsonError(err instanceof Error ? err.message : "Failed to parse JSON.");
    }
  }

  function onFormatJson() {
    setJsonError("");
    try {
      const parsed = JSON.parse(jsonDraft);
      setJsonDraft(JSON.stringify(parsed, null, 2));
    } catch (err) {
      setJsonError(err instanceof Error ? err.message : "Invalid JSON.");
    }
  }

  async function onRunRuleTest() {
    setTestError("");
    try {
      const payload =
        editorTab === "json" ? JSON.parse(jsonDraft) : formToRulePayload(form, { strict: true }).payload;
      const parsedHeaders = parseJsonObject(testHeadersJson, "Test headers");
      const parsedQuery = parseJsonObject(testQueryJson, "Test query");
      const parsedState = parseJsonObject(testStateJson, "Test state");
      const normalizedPath = `/${String(testPath || "").replace(/^\/+/, "")}`;
      const normalizedHeaders = Object.fromEntries(
        Object.entries(parsedHeaders).map(([key, value]) => [String(key).toLowerCase(), String(value)])
      );
      const normalizedQuery = Object.fromEntries(
        Object.entries(parsedQuery).map(([key, value]) => [String(key), String(value)])
      );

      const result = await previewRule(
        payload,
        {
          method: testMethod,
          path: normalizedPath,
          host: testHost,
          client_ip: testClientIp,
          body: testBody,
          headers: normalizedHeaders,
          query: normalizedQuery,
          route_exists: testRouteExists,
          state_key: testStateKey,
          state: parsedState
        },
        apiBase
      );
      setTestTrace(result);
    } catch (err) {
      setTestTrace(null);
      setTestError(err instanceof Error ? err.message : "Failed to run rule test.");
    }
  }

  function renderInspector() {
    if (selectedNodeId === "meta") {
      return (
        <div className="rule-inspector-fields">
          <h4>Rule Meta</h4>
          <label>
            Name
            <input
              type="text"
              value={form.name}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, name: event.target.value }))
              }
            />
          </label>
          <label>
            Priority
            <input
              type="number"
              value={form.priority}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, priority: event.target.value }))
              }
            />
          </label>
          <label className="rule-enable-checkbox">
            <input
              type="checkbox"
              checked={form.enabled}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, enabled: event.target.checked }))
              }
            />
            Enabled
          </label>
        </div>
      );
    }

    if (selectedNodeId === "match") {
      return (
        <div className="rule-inspector-fields">
          <h4>When / Match</h4>
          <label>
            Stage
            <select
              value={form.stage}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, stage: event.target.value }))
              }
            >
              <option value="pre">pre</option>
              <option value="post">post</option>
            </select>
          </label>
          <label>
            Method Regex
            <input
              type="text"
              value={form.methodRegex}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, methodRegex: event.target.value }))
              }
            />
          </label>
          <label>
            Path Regex
            <input
              type="text"
              value={form.pathRegex}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, pathRegex: event.target.value }))
              }
            />
          </label>
          <label>
            Host Regex
            <input
              type="text"
              value={form.hostRegex}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, hostRegex: event.target.value }))
              }
            />
          </label>
          <label>
            Body Regex
            <input
              type="text"
              value={form.bodyRegex}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, bodyRegex: event.target.value }))
              }
            />
          </label>
          <label>
            Extra Match JSON (loose)
            <textarea
              rows={7}
              value={form.extraMatchJson}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, extraMatchJson: event.target.value }))
              }
            />
          </label>
        </div>
      );
    }

    return (
      <div className="rule-inspector-fields">
        <h4>Then / Action</h4>
        <label>
          Status Code
          <input
            type="number"
            min="100"
            max="599"
            value={form.statusCode}
            onChange={(event) =>
              setForm((prev) => ({ ...prev, statusCode: event.target.value }))
            }
          />
        </label>
        <label>
          Content Type
          <input
            type="text"
            value={form.contentType}
            onChange={(event) =>
              setForm((prev) => ({ ...prev, contentType: event.target.value }))
            }
          />
        </label>
        <label>
          Response Body
          <textarea
            rows={4}
            value={form.responseBody}
            onChange={(event) =>
              setForm((prev) => ({ ...prev, responseBody: event.target.value }))
            }
          />
        </label>
        <label>
          Forward URL (optional)
          <input
            type="url"
            value={form.forwardUrl}
            onChange={(event) =>
              setForm((prev) => ({ ...prev, forwardUrl: event.target.value }))
            }
          />
        </label>
        <label>
          Forward Method
          <select
            value={form.forwardMethod}
            onChange={(event) =>
              setForm((prev) => ({ ...prev, forwardMethod: event.target.value }))
            }
          >
            <option value="POST">POST</option>
            <option value="PUT">PUT</option>
            <option value="PATCH">PATCH</option>
            <option value="GET">GET</option>
          </select>
        </label>
        <label>
          Extra Action JSON (loose)
          <textarea
            rows={7}
            value={form.extraActionJson}
            onChange={(event) =>
              setForm((prev) => ({ ...prev, extraActionJson: event.target.value }))
            }
          />
        </label>
      </div>
    );
  }

  return (
    <section>
      <h2>IFTTT Rule Builder</h2>
      <p>
        Diagram + JSON are bidirectional: edit either side and apply to sync.
      </p>

      <div className="rule-builder-shell">
        <aside className="rule-builder-list">
          <div className="rule-builder-list-head">
            <h3>Rules</h3>
            <button type="button" onClick={onNewRule}>
              New
            </button>
          </div>
          {loading && <p>Loading rules...</p>}
          {!loading && rules.length === 0 && <p>No rules yet.</p>}
          {rules.map((rule) => (
            <button
              key={rule.id}
              type="button"
              className={`rule-item-btn${selectedRuleId === rule.id ? " active" : ""}`}
              onClick={() => onSelectRule(rule)}
            >
              {rule.name} {rule.enabled ? "" : "(disabled)"}
            </button>
          ))}
        </aside>

        <div className="rule-builder-main">
          <div className="rule-tabs">
            <button
              type="button"
              className={editorTab === "diagram" ? "active" : ""}
              onClick={() => setEditorTab("diagram")}
            >
              Diagram
            </button>
            <button
              type="button"
              className={editorTab === "json" ? "active" : ""}
              onClick={() => {
                setEditorTab("json");
                setJsonDraft(graphToJson({ form }).json);
                setJsonError("");
              }}
            >
              JSON
            </button>
          </div>

          {editorTab === "diagram" ? (
            <div className="rule-flow-grid">
              <div className="rule-flow-canvas">
                <ReactFlow
                  nodes={nodes}
                  edges={edges}
                  onNodesChange={onNodesChange}
                  onEdgesChange={onEdgesChange}
                  onNodeClick={(_, node) => setSelectedNodeId(node.id)}
                  fitView
                  minZoom={0.4}
                  maxZoom={1.8}
                >
                  <Background gap={16} />
                  {/* <MiniMap pannable zoomable /> */}
                  <Controls />
                </ReactFlow>
              </div>
              <aside className="rule-inspector">{renderInspector()}</aside>
            </div>
          ) : (
            <div className="rule-json-editor">
              <textarea
                value={jsonDraft}
                onChange={(event) => setJsonDraft(event.target.value)}
                rows={24}
              />
              <div className="rule-json-actions">
                <button type="button" onClick={onApplyJson}>
                  Apply To Diagram
                </button>
                <button type="button" onClick={onFormatJson}>
                  Format JSON
                </button>
              </div>
              {jsonError && <p className="error">{jsonError}</p>}
            </div>
          )}

          <div className="rule-actions">
            <button type="button" onClick={onSaveRule} disabled={saving}>
              {saving ? "Saving..." : selectedRuleId ? "Update Rule" : "Create Rule"}
            </button>
            <button
              type="button"
              className="danger"
              onClick={onDeleteRule}
              disabled={saving || !selectedRuleId}
            >
              Delete Rule
            </button>
          </div>

          {error && <p className="error">{error}</p>}
          {preview.error && <p className="error">Preview: {preview.error}</p>}

          <section className="rule-preview">
            <h3>Generated Payload</h3>
            <pre>{JSON.stringify(preview.payload, null, 2)}</pre>
          </section>

          <section className="rule-preview rule-test-runner">
            <h3>Rule Test Runner</h3>
            <p>Preview this rule against a sample request and inspect each decision step.</p>
            <p>
              <strong>Loaded Filters:</strong>{" "}
              {availableFilters.length > 0 ? availableFilters.join(", ") : "No filters loaded"}
            </p>
            <div className="rule-test-grid">
              <label>
                Method
                <select value={testMethod} onChange={(event) => setTestMethod(event.target.value)}>
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
                  value={testPath}
                  onChange={(event) => setTestPath(event.target.value)}
                  placeholder="/demo"
                />
              </label>
              <label>
                Host
                <input
                  type="text"
                  value={testHost}
                  onChange={(event) => setTestHost(event.target.value)}
                  placeholder="localhost"
                />
              </label>
              <label>
                Client IP
                <input
                  type="text"
                  value={testClientIp}
                  onChange={(event) => setTestClientIp(event.target.value)}
                  placeholder="127.0.0.1"
                />
              </label>
            </div>
            <label>
              Route Exists (post-stage rules require existing route unless action creates one)
              <select
                value={testRouteExists ? "true" : "false"}
                onChange={(event) => setTestRouteExists(event.target.value === "true")}
              >
                <option value="true">true</option>
                <option value="false">false</option>
              </select>
            </label>
            <label>
              Body
              <textarea
                rows={4}
                value={testBody}
                onChange={(event) => setTestBody(event.target.value)}
                placeholder="Request body"
              />
            </label>
            <label>
              Headers JSON
              <textarea
                rows={4}
                value={testHeadersJson}
                onChange={(event) => setTestHeadersJson(event.target.value)}
                placeholder='{"content-type":"text/plain"}'
              />
            </label>
            <label>
              Query JSON
              <textarea
                rows={4}
                value={testQueryJson}
                onChange={(event) => setTestQueryJson(event.target.value)}
                placeholder='{"token":"abc"}'
              />
            </label>
            <label>
              State Key (optional seed for template context)
              <input
                type="text"
                value={testStateKey}
                onChange={(event) => setTestStateKey(event.target.value)}
                placeholder="token-123"
              />
            </label>
            <label>
              State JSON
              <textarea
                rows={4}
                value={testStateJson}
                onChange={(event) => setTestStateJson(event.target.value)}
                placeholder='{"__hops":1}'
              />
            </label>
            <div className="rule-actions">
              <button type="button" onClick={onRunRuleTest}>
                Run Rule Test
              </button>
            </div>
            {testError && <p className="error">{testError}</p>}
            {testTrace && (
              <div className="rule-test-output">
                <p>
                  <strong>Matched:</strong> {String(testTrace.matched)}
                </p>
                <p>
                  <strong>Trace:</strong>
                </p>
                <div className="rule-trace-list">
                  {testTrace.steps.map((step, index) => (
                    <div
                      key={`${step.label}-${index}`}
                      className={`rule-trace-item${step.ok ? " ok" : " fail"}`}
                    >
                      <strong>{step.ok ? "PASS" : "FAIL"}</strong> {step.label} - {step.detail}
                    </div>
                  ))}
                </div>
                <p>
                  <strong>Rendered Context:</strong>
                </p>
                <pre>{JSON.stringify(testTrace.rendered_context || {}, null, 2)}</pre>
                <p>
                  <strong>Rendered Action:</strong>
                </p>
                <pre>{JSON.stringify(testTrace.rendered_action || {}, null, 2)}</pre>
              </div>
            )}
          </section>
        </div>
      </div>
    </section>
  );
}
