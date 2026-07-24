/** Local control API client. */

export const API = localStorage.getItem("trenchApi") || "http://127.0.0.1:8742";

export async function fetchJSON(path, options = {}) {
  const r = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!r.ok) {
    let detail = r.statusText;
    try {
      const body = await r.json();
      detail = body.detail || JSON.stringify(body);
    } catch {
      /* ignore */
    }
    throw new Error(detail || r.statusText);
  }
  if (r.status === 204) return null;
  return r.json();
}

export async function postJSON(path, body = {}) {
  return fetchJSON(path, { method: "POST", body: JSON.stringify(body) });
}
