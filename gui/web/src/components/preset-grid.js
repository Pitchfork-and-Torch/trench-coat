/** One-click profile activation. */

import { fetchJSON, postJSON } from "./api.js";

export async function loadPresets(onActivated) {
  const grid = document.getElementById("preset-grid");
  if (!grid) return;
  try {
    const presets = await fetchJSON("/api/presets");
    const cfg = await fetchJSON("/api/config").catch(() => ({}));
    const active = cfg.active_chain || "";
    grid.innerHTML = "";
    presets.forEach((p) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "preset" + (p.name === active ? " active" : "");
      btn.setAttribute("aria-pressed", p.name === active ? "true" : "false");
      btn.innerHTML = `<strong>${escapeHtml(p.name.toUpperCase())}</strong>${escapeHtml(
        (p.description || "").slice(0, 90)
      )}${p.description && p.description.length > 90 ? "…" : ""}`;
      btn.addEventListener("click", async () => {
        btn.disabled = true;
        try {
          await postJSON("/api/chain/activate", { name: p.name });
          grid.querySelectorAll(".preset").forEach((el) => {
            el.classList.remove("active");
            el.setAttribute("aria-pressed", "false");
          });
          btn.classList.add("active");
          btn.setAttribute("aria-pressed", "true");
          if (onActivated) onActivated(p.name);
          const toast = document.getElementById("action-toast");
          if (toast) {
            toast.textContent = `Active chain → ${p.name}. Run trench up (or Engage) to apply live.`;
          }
        } catch (err) {
          const toast = document.getElementById("action-toast");
          if (toast) toast.textContent = `Activate failed: ${err.message}`;
        } finally {
          btn.disabled = false;
        }
      });
      grid.appendChild(btn);
    });
  } catch {
    grid.innerHTML =
      "<div class='preset'><strong>API OFFLINE</strong>Run <code>trench gui</code></div>";
  }
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}
