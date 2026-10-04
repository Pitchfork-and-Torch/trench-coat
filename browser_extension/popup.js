let lastView = companionStatus(null);

async function refresh() {
  const el = document.getElementById("status");
  const btn = document.getElementById("set-proxy");
  try {
    const r = await fetch("http://127.0.0.1:8742/api/status");
    if (!r.ok) throw new Error("status " + r.status);
    const j = await r.json();
    lastView = companionStatus(j);
    el.textContent = lastView.label;
  } catch {
    lastView = companionStatus(null);
    el.textContent = lastView.label;
  }
  btn.disabled = !lastView.proxyOk;
  btn.textContent = lastView.proxyOk
    ? "Use cloak SOCKS :" + (lastView.port || 1080)
    : "SOCKS waits until a cloak is up";
}

document.getElementById("set-proxy").onclick = async () => {
  if (!lastView.proxyOk) {
    document.getElementById("status").textContent = "SOCKS waits until a cloak is up.";
    return;
  }
  const port = lastView.port || 1080;
  try {
    await chrome.proxy.settings.set({
      value: {
        mode: "fixed_servers",
        rules: {
          singleProxy: { scheme: "socks5", host: "127.0.0.1", port: port },
        },
      },
      scope: "regular",
    });
    document.getElementById("status").textContent =
      "Browser proxy set to socks5://127.0.0.1:" + port;
  } catch (e) {
    document.getElementById("status").textContent = "Proxy set failed: " + e;
  }
};

refresh();
