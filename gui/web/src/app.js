/**
 * Trench Coat Command Nexus 2.0 — modular cyberpunk control surface.
 */

import { fetchJSON, postJSON } from "./components/api.js";
import { connectStatusStream } from "./components/ws.js";
import { createCityMap } from "./components/city-map.js";
import { applyStatus, refreshIdentity } from "./components/status-panel.js";
import { loadPresets } from "./components/preset-grid.js";
import { loadDossiers } from "./components/dossier-panel.js";

const NOIR = [
  "Rain on the glass. The city doesn't care who you are.",
  "The shadows have you covered… for now.",
  "Chain locked. Faces blur. Names dissolve.",
  "Neon signs lie. Packets don't have to.",
  "You are a rumor on a wet street.",
  "Fail-closed: if the chain dies, the coat holds the line.",
];

function $(id) {
  return document.getElementById(id);
}

function setNoir() {
  const el = $("noir-line");
  if (el) el.textContent = NOIR[Math.floor(Math.random() * NOIR.length)];
}

function toast(msg) {
  const el = $("action-toast");
  if (el) el.textContent = msg;
}

const canvas = $("city");
const map = canvas ? createCityMap(canvas) : null;

function onStatus(s) {
  window.__lastStatus = s;
  applyStatus(s);
  if (map) map.setStatus(s);
}

async function wireActions() {
  $("btn-legal")?.addEventListener("click", async () => {
    try {
      await postJSON("/api/legal/accept", {});
      toast("Legal notice accepted on this machine.");
    } catch (e) {
      toast(String(e.message || e));
    }
  });

  $("btn-newnym")?.addEventListener("click", async () => {
    try {
      const r = await postJSON("/api/tor/newnym", {});
      toast(r.ok ? "NEWNYM signalled." : `NEWNYM: ${r.message}`);
    } catch (e) {
      toast(String(e.message || e));
    }
  });

  $("btn-engage")?.addEventListener("click", async () => {
    try {
      await postJSON("/api/legal/accept", {});
      const r = await postJSON("/api/cloak/up", {
        accept_legal: true,
        wait_tor: 30,
      });
      toast(r.message || `Engage pid=${r.pid}`);
    } catch (e) {
      toast(String(e.message || e));
    }
  });

  $("btn-doctor")?.addEventListener("click", async () => {
    try {
      const r = await fetchJSON("/api/doctor");
      toast(`Doctor exit=${r.exit_code}: ${r.summary}`);
      const panel = $("doctor-summary");
      if (panel) {
        const fails = (r.checks || []).filter((c) => c.status === "fail" || c.status === "warn");
        panel.textContent = fails.length
          ? fails
              .slice(0, 6)
              .map((c) => `${c.status.toUpperCase()} ${c.title}: ${c.detail}`)
              .join("\n")
          : r.summary;
      }
    } catch (e) {
      toast(String(e.message || e));
    }
  });

  $("btn-refresh-dossiers")?.addEventListener("click", () => loadDossiers());
}

setNoir();
setInterval(setNoir, 12000);
loadPresets((name) => {
  toast(`Profile ${name} selected.`);
});
loadDossiers();
wireActions();
connectStatusStream(onStatus);
refreshIdentity(fetchJSON);
setInterval(() => refreshIdentity(fetchJSON), 15000);
