/** Circuit Desk: compose hops in Nexus without YAML. */

import { fetchJSON, postJSON, putJSON } from "./api.js";

const HOP_TYPES = ["tor", "socks5", "http", "https", "shadowsocks", "bridge"];

function $(id) {
  return document.getElementById(id);
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function hopRow(hop, index, total) {
  const typeOpts = HOP_TYPES.map((t) => {
    const sel = hop.type === t ? " selected" : "";
    return `<option value="${t}"${sel}>${t}</option>`;
  }).join("");
  const enabled = hop.enabled !== false;
  return `<li class="desk-hop" data-index="${index}" draggable="false">
    <button type="button" class="btn small desk-move" data-dir="-1" aria-label="Move hop up" ${index === 0 ? "disabled" : ""}>Up</button>
    <button type="button" class="btn small desk-move" data-dir="1" aria-label="Move hop down" ${index === total - 1 ? "disabled" : ""}>Down</button>
    <label class="desk-en">
      <input type="checkbox" class="desk-enabled" ${enabled ? "checked" : ""} aria-label="Enable hop ${escapeHtml(hop.id || "")}" />
    </label>
    <input class="desk-id" type="text" value="${escapeHtml(hop.id || "")}" aria-label="Hop id" maxlength="64" />
    <select class="desk-type" aria-label="Hop type">${typeOpts}</select>
    <input class="desk-host" type="text" value="${escapeHtml(hop.host || "127.0.0.1")}" aria-label="Hop host" />
    <input class="desk-port" type="number" min="1" max="65535" value="${Number(hop.port) || 9050}" aria-label="Hop port" />
    <input class="desk-label" type="text" value="${escapeHtml(hop.label || "")}" placeholder="label" aria-label="Hop label" />
    <button type="button" class="btn small desk-drop" aria-label="Drop hop">Drop</button>
  </li>`;
}

function readHopsFromDom(ul) {
  return [...ul.querySelectorAll(".desk-hop")].map((li) => ({
    id: li.querySelector(".desk-id").value.trim(),
    type: li.querySelector(".desk-type").value,
    host: li.querySelector(".desk-host").value.trim() || "127.0.0.1",
    port: Number(li.querySelector(".desk-port").value) || 9050,
    label: li.querySelector(".desk-label").value.trim() || null,
    enabled: li.querySelector(".desk-enabled").checked,
  }));
}

export function createCircuitDesk({ onDraft, onCanEngage, toast } = {}) {
  const ul = $("circuit-hops");
  const hint = $("desk-hint");
  const nameEl = $("desk-name");
  const templatesEl = $("desk-templates");
  let chain = {
    name: "custom-desk",
    hops: [],
    policy: { min_hops: 1, fail_closed: true },
    can_engage: false,
  };
  let saveTimer = null;
  let dirty = false;

  function setHint(text) {
    if (hint) hint.textContent = text;
  }

  function emit() {
    const hops = chain.hops || [];
    const enabled = hops.filter((h) => h.enabled !== false);
    const min = chain.policy?.min_hops ?? 1;
    const failClosed = chain.policy?.fail_closed !== false;
    const can = enabled.length >= min && (!failClosed || enabled.length >= 1);
    chain.can_engage = can;
    if (onDraft) onDraft(hops);
    if (onCanEngage) onCanEngage(can);
    const engage = $("btn-engage");
    if (engage) engage.disabled = !can;
    setHint(
      can
        ? `${enabled.length} enabled hop${enabled.length === 1 ? "" : "s"} ready.`
        : failClosed
          ? "Fail-closed: enable at least one hop before Engage."
          : `Need ${min} enabled hop(s) before Engage.`
    );
  }

  function renderHops() {
    if (!ul) return;
    const hops = chain.hops || [];
    if (!hops.length) {
      ul.innerHTML = `<li class="desk-empty">No hops. Import a template or add one.</li>`;
    } else {
      ul.innerHTML = hops.map((h, i) => hopRow(h, i, hops.length)).join("");
    }
    emit();
  }

  function collect() {
    if (!ul) return chain.hops;
    const hops = readHopsFromDom(ul).filter((h) => h.id);
    chain.hops = hops;
    if (nameEl && nameEl.value.trim()) chain.name = nameEl.value.trim();
    return hops;
  }

  async function persist() {
    collect();
    try {
      const body = {
        name: chain.name || "custom-desk",
        profile: chain.profile || "custom",
        description: chain.description || "Circuit Desk",
        hops: chain.hops,
        policy: chain.policy || undefined,
        tags: chain.tags || ["circuit-desk"],
      };
      const saved = await putJSON("/api/chain", body);
      chain = { ...chain, ...saved };
      dirty = false;
      if (nameEl) nameEl.value = chain.name || "";
      emit();
      return saved;
    } catch (err) {
      if (toast) toast(`Desk save failed: ${err.message}`);
      throw err;
    }
  }

  function scheduleSave() {
    dirty = true;
    collect();
    emit();
    if (saveTimer) clearTimeout(saveTimer);
    saveTimer = setTimeout(() => {
      persist().catch(() => {});
    }, 350);
  }

  async function reload() {
    try {
      const data = await fetchJSON("/api/chain");
      chain = { ...chain, ...data };
      if (nameEl) nameEl.value = chain.name || "";
      renderHops();
    } catch {
      setHint("API offline. Run trench gui.");
      if (onCanEngage) onCanEngage(false);
    }
  }

  async function loadTemplates() {
    if (!templatesEl) return;
    try {
      const rows = await fetchJSON("/api/templates");
      templatesEl.innerHTML = "";
      (rows || []).forEach((t) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "btn small desk-template";
        btn.textContent = t.title || t.id;
        btn.title = t.description || t.id;
        btn.addEventListener("click", async () => {
          try {
            const imported = await postJSON(`/api/templates/${encodeURIComponent(t.id)}/import`, {});
            chain = { ...chain, ...imported };
            if (nameEl) nameEl.value = chain.name || "";
            renderHops();
            if (toast) toast(`Imported ${imported.name || t.id} onto the desk.`);
          } catch (err) {
            if (toast) toast(`Import failed: ${err.message}`);
          }
        });
        templatesEl.appendChild(btn);
      });
    } catch {
      templatesEl.innerHTML = `<span class="dim">No templates</span>`;
    }
  }

  function addHop() {
    collect();
    const n = (chain.hops || []).length + 1;
    chain.hops = [
      ...(chain.hops || []),
      {
        id: `hop-${n}`,
        type: "socks5",
        host: "127.0.0.1",
        port: 1080,
        label: "",
        enabled: true,
      },
    ];
    renderHops();
    scheduleSave();
  }

  if (ul) {
    ul.addEventListener("click", (ev) => {
      const drop = ev.target.closest(".desk-drop");
      const move = ev.target.closest(".desk-move");
      const li = ev.target.closest(".desk-hop");
      if (!li) return;
      const idx = Number(li.dataset.index);
      collect();
      if (drop) {
        chain.hops.splice(idx, 1);
        renderHops();
        scheduleSave();
        return;
      }
      if (move) {
        const dir = Number(move.dataset.dir);
        const next = idx + dir;
        if (next < 0 || next >= chain.hops.length) return;
        const copy = chain.hops.slice();
        const [item] = copy.splice(idx, 1);
        copy.splice(next, 0, item);
        chain.hops = copy;
        renderHops();
        scheduleSave();
      }
    });
    ul.addEventListener("change", () => {
      collect();
      emit();
      scheduleSave();
    });
    ul.addEventListener("keydown", (ev) => {
      const li = ev.target.closest(".desk-hop");
      if (!li) return;
      const idx = Number(li.dataset.index);
      if (ev.key === "Delete" && ev.target.classList.contains("desk-id")) {
        collect();
        chain.hops.splice(idx, 1);
        renderHops();
        scheduleSave();
      }
      if ((ev.key === "ArrowUp" || ev.key === "ArrowDown") && ev.altKey) {
        ev.preventDefault();
        collect();
        const dir = ev.key === "ArrowUp" ? -1 : 1;
        const next = idx + dir;
        if (next < 0 || next >= chain.hops.length) return;
        const copy = chain.hops.slice();
        const [item] = copy.splice(idx, 1);
        copy.splice(next, 0, item);
        chain.hops = copy;
        renderHops();
        scheduleSave();
      }
    });
  }

  $("btn-add-hop")?.addEventListener("click", addHop);
  $("btn-desk-save")?.addEventListener("click", () => {
    persist()
      .then(() => toast && toast("Circuit saved."))
      .catch(() => {});
  });
  nameEl?.addEventListener("change", scheduleSave);

  loadTemplates();
  reload();

  return {
    reload,
    persist,
    getChain: () => chain,
    isDirty: () => dirty,
  };
}
