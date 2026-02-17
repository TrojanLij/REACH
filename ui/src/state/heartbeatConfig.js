export const HEARTBEAT_STORAGE_KEY = "reach_heartbeat_seconds";
export const DEFAULT_HEARTBEAT_SECONDS = 5;

export function readHeartbeatSeconds() {
  try {
    const raw = window.localStorage.getItem(HEARTBEAT_STORAGE_KEY);
    const parsed = Number(raw);
    if (Number.isFinite(parsed) && parsed >= 1 && parsed <= 120) {
      return parsed;
    }
    return DEFAULT_HEARTBEAT_SECONDS;
  } catch {
    return DEFAULT_HEARTBEAT_SECONDS;
  }
}
