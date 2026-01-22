import { API_BASE } from "./auth";

const KEY = "synopsis.user";

export function getStoredUser() {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function storeUser(user) {
  try {
    if (!user) {
      localStorage.removeItem(KEY);
      return;
    }
    localStorage.setItem(KEY, JSON.stringify(user));
  } catch {
    // ignore
  }
}

export async function fetchMe() {
  const res = await fetch(`${API_BASE}/api/auth/me/`, {
    method: "GET",
    credentials: "include",
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok || !data?.ok) return null;
  return data.user || null;
}

export async function logout() {
  try {
    await fetch(`${API_BASE}/api/auth/logout/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({}),
    });
  } finally {
    storeUser(null);
  }
}
