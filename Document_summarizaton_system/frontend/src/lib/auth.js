const DEV_BACKEND_PORT = 8000;

function getDefaultApiBase() {
  try {
    const host = window?.location?.hostname;
    // Prefer localhost in local dev (some environments may not accept
    // 127.0.0.1 connections even if localhost works).
    if (host === "localhost" || host === "127.0.0.1") {
      return `http://localhost:${DEV_BACKEND_PORT}`;
    }
  } catch {
    // ignore
  }
  return `http://localhost:${DEV_BACKEND_PORT}`;
}

const API_BASE = import.meta?.env?.VITE_API_BASE || getDefaultApiBase();

export { API_BASE };
