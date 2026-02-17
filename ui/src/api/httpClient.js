import { DEFAULT_API_BASE } from "../state/ApiConfigContext";

function normalizeBase(apiBase) {
  return (apiBase || DEFAULT_API_BASE).replace(/\/$/, "");
}

export async function getJson(path, options = {}) {
  const { apiBase, ...fetchOptions } = options;
  const response = await fetch(`${normalizeBase(apiBase)}${path}`, {
    headers: {
      Accept: "application/json"
    },
    ...fetchOptions
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`${response.status} ${response.statusText}: ${body}`);
  }

  return response.json();
}

export async function postJson(path, body, options = {}) {
  const { apiBase, ...fetchOptions } = options;
  const response = await fetch(`${normalizeBase(apiBase)}${path}`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json"
    },
    body: JSON.stringify(body),
    ...fetchOptions
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`${response.status} ${response.statusText}: ${errorBody}`);
  }

  return response.json();
}

export async function patchJson(path, body, options = {}) {
  const { apiBase, ...fetchOptions } = options;
  const response = await fetch(`${normalizeBase(apiBase)}${path}`, {
    method: "PATCH",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json"
    },
    body: JSON.stringify(body),
    ...fetchOptions
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`${response.status} ${response.statusText}: ${errorBody}`);
  }

  return response.json();
}

export async function deleteJson(path, options = {}) {
  const { apiBase, ...fetchOptions } = options;
  const response = await fetch(`${normalizeBase(apiBase)}${path}`, {
    method: "DELETE",
    headers: {
      Accept: "application/json"
    },
    ...fetchOptions
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`${response.status} ${response.statusText}: ${errorBody}`);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}
