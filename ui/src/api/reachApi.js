import { deleteJson, getJson, patchJson, postJson } from "./httpClient";

export function getHealth(apiBase) {
  return getJson("/api/health", { apiBase });
}

export function listRoutes(apiBase) {
  return getJson("/api/routes", { apiBase });
}

export function listLogs(limit = 20, apiBase) {
  return getJson(`/api/logs?since_id=0&limit=${limit}`, { apiBase });
}

export function fetchLogs({
  sinceId = 0,
  limit = 100,
  protocol = "",
  apiBase
} = {}) {
  const params = new URLSearchParams();
  params.set("since_id", String(sinceId));
  params.set("limit", String(limit));
  if (protocol) {
    params.set("protocol", protocol);
  }
  return getJson(`/api/logs?${params.toString()}`, { apiBase });
}

export function createRoute(routePayload, apiBase) {
  return postJson("/api/routes", routePayload, { apiBase });
}

export function deleteRoute(routeId, apiBase) {
  return deleteJson(`/api/routes/${routeId}`, { apiBase });
}

export function updateRoute(routeId, routePayload, apiBase) {
  return patchJson(`/api/routes/${routeId}`, routePayload, { apiBase });
}

export function listRules(apiBase) {
  return getJson("/api/rules", { apiBase });
}

export function createRule(rulePayload, apiBase) {
  return postJson("/api/rules", rulePayload, { apiBase });
}

export function updateRule(ruleId, rulePayload, apiBase) {
  return patchJson(`/api/rules/${ruleId}`, rulePayload, { apiBase });
}

export function deleteRule(ruleId, apiBase) {
  return deleteJson(`/api/rules/${ruleId}`, { apiBase });
}

export function listDnsZones(apiBase) {
  return getJson("/api/dns/zones", { apiBase });
}

export function createDnsZone(zonePayload, apiBase) {
  return postJson("/api/dns/zones", zonePayload, { apiBase });
}

export function updateDnsZone(zoneId, zonePayload, apiBase) {
  return patchJson(`/api/dns/zones/${zoneId}`, zonePayload, { apiBase });
}

export function deleteDnsZone(zoneId, apiBase) {
  return deleteJson(`/api/dns/zones/${zoneId}`, { apiBase });
}
