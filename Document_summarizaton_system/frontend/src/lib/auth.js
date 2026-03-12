const DEV_BACKEND_PORT = 8000;

function getDefaultApiBase() {
  try {
    const host = window?.location?.hostname;
    // Keep frontend/backend hostnames aligned so session cookies stay same-site.
    // If frontend is opened via 127.0.0.1, call backend on 127.0.0.1 as well.
    // If frontend is opened via localhost, call backend on localhost.
    if (host === "localhost") {
      return `http://localhost:${DEV_BACKEND_PORT}`;
    }
    if (host === "127.0.0.1") {
      return `http://127.0.0.1:${DEV_BACKEND_PORT}`;
    }
  } catch {
    // ignore
  }
  return `http://localhost:${DEV_BACKEND_PORT}`;
}

const API_BASE = import.meta?.env?.VITE_API_BASE || getDefaultApiBase();

export { API_BASE };
