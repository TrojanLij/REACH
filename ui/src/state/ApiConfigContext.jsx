import { createContext, useContext, useMemo, useState } from "react";

const DEFAULT_API_BASE =
  import.meta.env.VITE_REACH_API_BASE || "http://127.0.0.1:8001";
const STORAGE_KEY = "reach_api_base";

function readStoredApiBase() {
  try {
    const value = window.localStorage.getItem(STORAGE_KEY);
    return value || DEFAULT_API_BASE;
  } catch {
    return DEFAULT_API_BASE;
  }
}

const ApiConfigContext = createContext({
  apiBase: DEFAULT_API_BASE,
  setApiBase: () => {}
});

export function ApiConfigProvider({ children }) {
  const [apiBase, setApiBaseState] = useState(() => readStoredApiBase());

  function setApiBase(nextValue) {
    const trimmed = nextValue.trim();
    const normalized = (trimmed || DEFAULT_API_BASE).replace(/\/$/, "");
    setApiBaseState(normalized);
    try {
      window.localStorage.setItem(STORAGE_KEY, normalized);
    } catch {
      // no-op
    }
  }

  const value = useMemo(() => ({ apiBase, setApiBase }), [apiBase]);

  return (
    <ApiConfigContext.Provider value={value}>
      {children}
    </ApiConfigContext.Provider>
  );
}

export function useApiConfig() {
  return useContext(ApiConfigContext);
}

export { DEFAULT_API_BASE };
