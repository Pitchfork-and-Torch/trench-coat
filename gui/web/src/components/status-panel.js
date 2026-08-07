/** Cloak status KV + metrics + live region. */

function fmtBytes(n) {
  if (n == null || Number.isNaN(n)) return "0 B";
  if (n < 1024) return `${n} B`;
  if (n < 1024 ** 2) return `${(n / 1024).toFixed(1)} KB`;
  if (n < 1024 ** 3) return `${(n / 1024 ** 2).toFixed(1)} MB`;
  return `${(n / 1024 ** 3).toFixed(2)} GB`;
}

function $(id) {
  return document.getElementById(id);
}

let lastPill = "";

export function applyStatus(s) {
  const pill = $("status-pill");
  const live = $("live-region");
  let label = "OFFLINE";
  if (s.fail_closed_tripped) label = "HOLD";
  else if (s.running) label = "CLOAKED";

  if (pill) {
    pill.textContent = label;
    pill.classList.toggle("on", label === "CLOAKED");
    pill.classList.toggle("hold", label === "HOLD");
  }
  if (live && label !== lastPill) {
    live.textContent = `Cloak status: ${label}`;
    lastPill = label;
  }

  const set = (id, v) => {
    const el = $(id);
    if (el) el.textContent = v;
  };
  set("kv-chain", s.chain_name || "—");
  set("kv-profile", s.profile || "—");
  set("kv-listen", s.listen || "—");
  set("kv-ks", s.kill_switch_active ? "ARMED" : "OFF");
  set(
    "kv-fc",
    s.fail_closed_tripped ? "TRIPPED" : s.refuse_direct !== false ? "ARMED" : "OFF"
  );
  set("m-in", fmtBytes(s.bytes_in || 0));
  set("m-out", fmtBytes(s.bytes_out || 0));
  set("m-conn", String(s.active_connections ?? s.connections ?? 0));
  set("m-refused", String(s.refused_connects ?? 0));

  const lat = s.snapshot?.total_latency_ms;
  set("kv-latency", lat != null ? `${Math.round(lat)} ms` : "—");

  const msg = $("status-messages");
  if (msg) {
    const lines = s.messages || [];
    msg.textContent = lines.slice(-3).join(" · ") || "—";
  }

  renderHops(s.snapshot?.hops || []);
}

export function renderHops(hops = []) {
  const ul = $("hop-list");
  if (!ul) return;
  ul.innerHTML = "";
  if (!hops.length) {
    ul.innerHTML =
      "<li><span class='dot unknown'></span><span>No hop telemetry</span><span>—</span></li>";
    return;
  }
  hops.forEach((h) => {
    const li = document.createElement("li");
    const health = h.health || "unknown";
    li.innerHTML = `
      <span class="dot ${health}"></span>
      <span>${escapeHtml(h.id || "?")}</span>
      <span>${h.latency_ms != null ? h.latency_ms + " ms" : "—"}</span>
    `;
    ul.appendChild(li);
  });
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

export async function refreshIdentity(fetchJSON) {
  try {
    const id = await fetchJSON("/api/identity?via=auto");
    const tor = await fetchJSON("/api/tor");
    const el = $("kv-identity");
    if (!el) return;
    if (id.is_tor === true) el.textContent = `TOR ${id.ip || ""}`.trim();
    else if (id.is_tor === false) el.textContent = `CLEAR ${id.ip || ""}`.trim();
    else el.textContent = id.ip || (tor.available ? "TOR SOCKS UP" : "—");
  } catch {
    /* API offline */
  }
}
