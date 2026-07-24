/** Status WebSocket with HTTP poll fallback. */

import { API, fetchJSON } from "./api.js";

export function connectStatusStream(onStatus) {
  let pollTimer = null;
  let ws = null;
  let stopped = false;

  async function pollOnce() {
    try {
      const s = await fetchJSON("/api/status");
      onStatus(s);
    } catch {
      onStatus({ running: false, messages: ["API offline — run trench gui"] });
    }
  }

  function startPoll() {
    if (pollTimer) return;
    pollOnce();
    pollTimer = setInterval(pollOnce, 2000);
  }

  function stopPoll() {
    if (pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
  }

  function connectWs() {
    if (stopped) return;
    try {
      const wsUrl = API.replace(/^http/, "ws") + "/ws/status";
      ws = new WebSocket(wsUrl);
      ws.onopen = () => stopPoll();
      ws.onmessage = (ev) => {
        try {
          onStatus(JSON.parse(ev.data));
        } catch {
          /* ignore bad frame */
        }
      };
      ws.onerror = () => {
        /* onclose handles reconnect */
      };
      ws.onclose = () => {
        startPoll();
        if (!stopped) setTimeout(connectWs, 3000);
      };
    } catch {
      startPoll();
    }
  }

  connectWs();

  return () => {
    stopped = true;
    stopPoll();
    if (ws) try { ws.close(); } catch { /* */ }
  };
}
