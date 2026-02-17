const KNOWN_MATCH_KEYS = new Set(["stage", "method", "path", "host", "body"]);
const KNOWN_ACTION_KEYS = new Set([
  "status_code",
  "content_type",
  "body",
  "response_body",
  "forward"
]);

export function defaultRuleForm() {
  return {
    name: "new-rule",
    enabled: true,
    priority: 100,
    stage: "post",
    methodRegex: "^GET$",
    pathRegex: "^/demo$",
    hostRegex: "",
    bodyRegex: "",
    extraMatchJson: "{}",
    statusCode: 200,
    contentType: "text/plain",
    responseBody: "ok",
    forwardUrl: "",
    forwardMethod: "POST",
    extraActionJson: "{}"
  };
}

function toPrettyJson(value) {
  return JSON.stringify(value, null, 2);
}

function extractExtras(source, knownKeys) {
  const extras = {};
  Object.entries(source || {}).forEach(([key, value]) => {
    if (!knownKeys.has(key)) {
      extras[key] = value;
    }
  });
  return extras;
}

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

function labelForNode(nodeId, form) {
  if (nodeId === "meta") {
    return `${form.name} | p=${form.priority} | ${form.enabled ? "enabled" : "disabled"}`;
  }
  if (nodeId === "match") {
    return `${form.methodRegex || "*"} ${form.pathRegex || "*"} (${form.stage})`;
  }
  return `${form.statusCode} ${form.contentType}`;
}

function buildBaseMatch(state) {
  const match = {};
  if (state.methodRegex.trim()) {
    match.method = state.methodRegex.trim();
  }
  if (state.pathRegex.trim()) {
    match.path = state.pathRegex.trim();
  }
  if (state.hostRegex.trim()) {
    match.host = state.hostRegex.trim();
  }
  if (state.bodyRegex.trim()) {
    match.body = state.bodyRegex.trim();
  }
  match.stage = state.stage;
  return match;
}

function buildBaseAction(state) {
  const action = {
    status_code: Number(state.statusCode),
    content_type: state.contentType.trim() || "text/plain",
    body: state.responseBody
  };
  if (state.forwardUrl.trim()) {
    action.forward = {
      url: state.forwardUrl.trim(),
      method: state.forwardMethod
    };
  }
  return action;
}

export function formToRulePayload(state, { strict = false } = {}) {
  const payload = {
    name: state.name.trim() || "new-rule",
    enabled: Boolean(state.enabled),
    priority: Number(state.priority),
    match: buildBaseMatch(state),
    action: buildBaseAction(state)
  };

  try {
    const extraMatch = parseJsonObject(state.extraMatchJson, "Extra Match JSON");
    const extraAction = parseJsonObject(state.extraActionJson, "Extra Action JSON");
    payload.match = { ...payload.match, ...extraMatch };
    payload.action = { ...payload.action, ...extraAction };
    return { payload, error: "" };
  } catch (err) {
    if (strict) {
      throw err;
    }
    return {
      payload,
      error: err instanceof Error ? err.message : "Invalid JSON override."
    };
  }
}

export function rulePayloadToForm(rule) {
  const match = rule.match || {};
  const action = rule.action || {};
  const extraMatch = extractExtras(match, KNOWN_MATCH_KEYS);
  const extraAction = extractExtras(action, KNOWN_ACTION_KEYS);

  return {
    name: rule.name || "",
    enabled: Boolean(rule.enabled),
    priority: rule.priority ?? 100,
    stage: match.stage || "post",
    methodRegex: match.method || "^GET$",
    pathRegex: match.path || "^/demo$",
    hostRegex: match.host || "",
    bodyRegex: match.body || "",
    extraMatchJson: toPrettyJson(extraMatch),
    statusCode: action.status_code ?? 200,
    contentType: action.content_type || "text/plain",
    responseBody: action.body ?? action.response_body ?? "ok",
    forwardUrl: action.forward?.url || "",
    forwardMethod: action.forward?.method || "POST",
    extraActionJson: toPrettyJson(extraAction)
  };
}

export function formToGraphNodes(form, baseNodes) {
  return baseNodes.map((node) => ({
    ...node,
    data: {
      ...(node.data || {}),
      label: labelForNode(node.id, form)
    }
  }));
}

export function graphToJson({ form }) {
  const { payload, error } = formToRulePayload(form, { strict: false });
  return { payload, error, json: JSON.stringify(payload, null, 2) };
}

export function jsonToGraph(input, baseNodes) {
  const payload = typeof input === "string" ? JSON.parse(input) : input;
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    throw new Error("Rule JSON must be an object.");
  }
  const form = rulePayloadToForm(payload);
  const nodes = formToGraphNodes(form, baseNodes);
  return { payload, form, nodes };
}
