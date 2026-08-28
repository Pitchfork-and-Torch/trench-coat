async function refresh() {
  const el = document.getElementById("status");
  try {
    const r = await fetch("http://127.0.0.1:8742/api/status");
    const j = await r.json();
    el.textContent = j.running
      ? `Cloaked · ${j.listen || "socks"}`
      : "Engine offline — run trench gui / trench up";
  } catch {
    el.textContent = "API unreachable (start trench gui)";
  }
}

document.getElementById("set-proxy").onclick = async () => {
  // MV3 proxy settings API — requires proxy permission
  try {
    await chrome.proxy.settings.set({
      value: {
        mode: "fixed_servers",
        rules: {
          singleProxy: { scheme: "socks5", host: "127.0.0.1", port: 1080 },
        },
      },
      scope: "regular",
    });
    document.getElementById("status").textContent = "Browser proxy → socks5://127.0.0.1:1080";
  } catch (e) {
    document.getElementById("status").textContent = "Proxy set failed: " + e;
  }
};

refresh();
