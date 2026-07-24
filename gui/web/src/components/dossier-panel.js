/** Session dossier list + detail viewer. */

import { fetchJSON } from "./api.js";

function escapeHtml(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

export async function loadDossiers() {
  const list = document.getElementById("dossier-list");
  const detail = document.getElementById("dossier-detail");
  if (!list) return;
  try {
    const data = await fetchJSON("/api/sessions");
    const sessions = data.sessions || [];
    list.innerHTML = "";
    if (!sessions.length) {
      list.innerHTML = "<li class='dim'>No dossiers yet — engage a session with trench up</li>";
      return;
    }
    sessions.slice(0, 12).forEach((s) => {
      const li = document.createElement("li");
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "dossier-item";
      const when = s.started_at
        ? new Date(s.started_at * 1000).toLocaleString()
        : s.session_id;
      btn.textContent = `${s.session_id} · ${s.events ?? 0} events · ${when}`;
      btn.addEventListener("click", async () => {
        try {
          const full = await fetchJSON(`/api/sessions/${encodeURIComponent(s.session_id)}`);
          if (!detail) return;
          const events = (full.events || [])
            .slice(-20)
            .map(
              (e) =>
                `<tr><td>${escapeHtml(
                  e.ts ? new Date(e.ts * 1000).toLocaleTimeString() : ""
                )}</td><td class="kind">${escapeHtml(e.kind)}</td><td>${escapeHtml(
                  e.message
                )}</td></tr>`
            )
            .join("");
          detail.innerHTML = `
            <h3>DOSSIER // ${escapeHtml(full.session_id || s.session_id)}</h3>
            <table class="dossier-table">
              <thead><tr><th>TIME</th><th>EVENT</th><th>NOTE</th></tr></thead>
              <tbody>${events || "<tr><td colspan=3>No events</td></tr>"}</tbody>
            </table>`;
        } catch (err) {
          if (detail) detail.textContent = `Load failed: ${err.message}`;
        }
      });
      li.appendChild(btn);
      list.appendChild(li);
    });
  } catch {
    list.innerHTML = "<li class='dim'>Sessions API offline</li>";
  }
}
