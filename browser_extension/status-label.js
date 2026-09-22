// Honest companion label for /api/status. Not a cloak claim.
function listenPort(listen) {
  var match = String(listen || "").match(/:(\d+)\s*$/);
  if (!match) return null;
  var port = Number(match[1]);
  if (!Number.isInteger(port) || port < 1 || port > 65535) return null;
  return port;
}

function companionStatus(status) {
  var row = status && typeof status === "object" ? status : {};
  var listen = row.listen ? String(row.listen) : "";
  var hops = row.snapshot && Array.isArray(row.snapshot.hops) ? row.snapshot.hops : [];
  var healths = hops.map(function (hop) {
    return String((hop && hop.health) || "").toLowerCase();
  });
  var dead = healths.indexOf("dead") >= 0;
  var degraded =
    healths.indexOf("degraded") >= 0 ||
    (row.snapshot && row.snapshot.healthy === false);
  var label;
  var proxyOk = false;
  if (row.stale) {
    label = "Stale status. Not cloaked.";
  } else if (row.pending) {
    label = "Pending. Cloak entry not confirmed.";
  } else if (row.fail_closed_tripped) {
    label = "Fail closed. Not cloaked.";
  } else if (row.running && dead) {
    label = listen ? "Hop down. Not cloaked. " + listen : "Hop down. Not cloaked.";
  } else if (row.running && degraded) {
    label = listen
      ? "Degraded. Listener up, hop not healthy. " + listen
      : "Degraded. Listener up, hop not healthy.";
    proxyOk = true;
  } else if (row.running) {
    label = "Cloaked | " + (listen || "socks");
    proxyOk = true;
  } else if (row.listen_port_open) {
    label = "Port open. Not a cloak.";
  } else {
    label = "Engine offline. Run trench gui or trench up.";
  }
  return { label: label, proxyOk: proxyOk, port: listenPort(listen) };
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { companionStatus: companionStatus, listenPort: listenPort };
}
