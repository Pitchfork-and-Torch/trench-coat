/**
 * City map circuit visualization — real hop id/health/latency on nodes.
 */

const HEALTH_HOT = new Set(["healthy", "ok", "degraded"]);

export function createCityMap(canvas) {
  const ctx = canvas.getContext("2d");
  let packets = [];
  let hopNodes = [];
  let trail = [];
  let lastStatus = {};
  const t0 = Date.now();
  const reduced =
    typeof matchMedia === "function" &&
    matchMedia("(prefers-reduced-motion: reduce)").matches;

  function layoutFromStatus(status) {
    const hops = status?.snapshot?.hops || [];
    const w = canvas.width;
    const h = canvas.height;
    const margin = 90;
    const mid = hops.length
      ? hops.map((hop, i) => {
          const x = margin + ((w - margin * 2) * (i + 1)) / (hops.length + 1);
          const y = h * (0.38 + 0.22 * Math.sin(i * 1.3));
          const lat =
            hop.latency_ms != null ? `${Math.round(hop.latency_ms)}ms` : "";
          return {
            x,
            y,
            label: hop.id || `H${i + 1}`,
            sub: lat,
            health: hop.health || "unknown",
            pulse: Math.random(),
          };
        })
      : Array.from({ length: Math.max(status?.proxy_chain?.length || 1, 1) }, (_, i) => ({
          x: margin + ((w - margin * 2) * (i + 1)) / 2,
          y: h * 0.5,
          label: `H${i + 1}`,
          sub: "",
          health: status?.running ? "healthy" : "unknown",
          pulse: 0,
        }));

    hopNodes = [
      { x: 40, y: h * 0.72, label: "YOU", sub: "", health: "local", pulse: 0 },
      ...mid,
      {
        x: w - 40,
        y: h * 0.55,
        label: "NET",
        sub: status?.fail_closed_tripped ? "HOLD" : "",
        health: status?.fail_closed_tripped ? "dead" : "exit",
        pulse: 0,
      },
    ];
  }

  function spawnPacket() {
    if (hopNodes.length < 2 || reduced) return;
    packets.push({
      i: 0,
      t: 0,
      speed: 0.008 + Math.random() * 0.01,
      hue: Math.random() > 0.5 ? 150 : 320,
    });
  }

  function nodeHot(n, status) {
    if (status?.fail_closed_tripped && n.label !== "YOU") return false;
    if (n.health === "local") return !!status?.running;
    if (n.health === "exit") return !!status?.running && !status?.fail_closed_tripped;
    return status?.running && HEALTH_HOT.has(String(n.health).toLowerCase());
  }

  function drawBuilding(x, y, label, sub, hot, dead) {
    const bw = 30;
    const bh = 52 + Math.sin(x) * 10;
    ctx.fillStyle = dead ? "#2a0810" : hot ? "#00ff9f22" : "#12081a";
    ctx.strokeStyle = dead ? "#ff3366" : hot ? "#00ff9f" : "#ff00aa66";
    ctx.lineWidth = dead ? 2 : 1.5;
    ctx.beginPath();
    ctx.rect(x - bw / 2, y - bh, bw, bh);
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = dead ? "#ff336688" : hot ? "#00ff9faa" : "#ff00aa44";
    for (let r = 0; r < 3; r++) {
      for (let c = 0; c < 2; c++) {
        ctx.fillRect(x - 8 + c * 10, y - bh + 8 + r * 12, 6, 6);
      }
    }
    ctx.fillStyle = "#c8f5e0";
    ctx.font = "10px monospace";
    ctx.textAlign = "center";
    const short = label.length > 12 ? label.slice(0, 11) + "…" : label;
    ctx.fillText(short, x, y + 14);
    if (sub) {
      ctx.fillStyle = dead ? "#ff3366" : "#5a7a6a";
      ctx.font = "9px monospace";
      ctx.fillText(sub, x, y + 26);
    }
  }

  function draw(status) {
    lastStatus = status || {};
    const hops = lastStatus?.snapshot?.hops || [];
    const expected = (hops.length || lastStatus?.proxy_chain?.length || 1) + 2;
    if (hopNodes.length !== expected) layoutFromStatus(lastStatus);

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const t = (Date.now() - t0) / 1000;
    const tripped = !!lastStatus.fail_closed_tripped;

    // perspective floor grid
    ctx.strokeStyle = tripped ? "#ff336618" : "#00ff9f18";
    ctx.lineWidth = 1;
    const horizon = canvas.height * 0.42;
    for (let i = 0; i < 18; i++) {
      const y = horizon + Math.pow(i / 17, 1.6) * (canvas.height - horizon);
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(canvas.width, y);
      ctx.stroke();
    }
    for (let i = -12; i <= 12; i++) {
      ctx.beginPath();
      ctx.moveTo(canvas.width / 2 + i * 8, horizon);
      ctx.lineTo(canvas.width / 2 + i * 70, canvas.height);
      ctx.stroke();
    }

    // skyline
    ctx.fillStyle = "#0a0610";
    ctx.beginPath();
    ctx.moveTo(0, canvas.height);
    for (let x = 0; x < canvas.width; x += 16) {
      const hh = 48 + ((x * 17 + Math.sin(t + x * 0.01) * 6) % 95);
      ctx.lineTo(x, canvas.height - hh);
    }
    ctx.lineTo(canvas.width, canvas.height);
    ctx.fill();

    // fabric
    ctx.strokeStyle = tripped ? "#ff336688" : "#ff00aa44";
    ctx.lineWidth = 2;
    ctx.beginPath();
    hopNodes.forEach((n, i) => {
      const y = n.y - 50 + Math.sin(t * 2 + i) * 3;
      if (i === 0) ctx.moveTo(n.x, y);
      else {
        const prev = hopNodes[i - 1];
        const cpx = (prev.x + n.x) / 2;
        const cpy = Math.min(prev.y, n.y) - 80;
        ctx.quadraticCurveTo(cpx, cpy, n.x, y);
      }
    });
    ctx.stroke();

    hopNodes.forEach((n, i) => {
      const dead = String(n.health).toLowerCase() === "dead" || (tripped && n.label !== "YOU");
      const hot = nodeHot(n, lastStatus);
      drawBuilding(n.x, n.y + Math.sin(t + i) * 2, n.label, n.sub, hot, dead);
    });

    if (!reduced) {
      packets.forEach((p) => {
        p.t += p.speed;
        if (p.t >= 1) {
          p.i += 1;
          p.t = 0;
          if (p.i >= hopNodes.length - 1) p.dead = true;
        }
        if (p.dead) return;
        const a = hopNodes[p.i];
        const b = hopNodes[p.i + 1];
        const x = a.x + (b.x - a.x) * p.t;
        const y = a.y - 50 + (b.y - a.y) * p.t + Math.sin(t * 4) * 2;
        trail.push({ x, y, life: 1, hue: p.hue });
        ctx.beginPath();
        ctx.fillStyle = `hsla(${p.hue}, 100%, 60%, 0.95)`;
        ctx.shadowColor = ctx.fillStyle;
        ctx.shadowBlur = 14;
        ctx.arc(x, y, 3.5, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0;
      });
      packets = packets.filter((p) => !p.dead);
      trail = trail.filter((tr) => {
        tr.life -= 0.04;
        if (tr.life <= 0) return false;
        ctx.beginPath();
        ctx.fillStyle = `hsla(${tr.hue}, 100%, 55%, ${tr.life * 0.35})`;
        ctx.arc(tr.x, tr.y, 2, 0, Math.PI * 2);
        ctx.fill();
        return true;
      });
    }

    if (tripped) {
      ctx.fillStyle = "rgba(255, 51, 102, 0.12)";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = "#ff3366";
      ctx.font = "bold 14px monospace";
      ctx.textAlign = "center";
      ctx.fillText("FAIL-CLOSED — NO CLEARNET", canvas.width / 2, 28);
    }
  }

  function loop() {
    draw(lastStatus);
    if (!reduced && Math.random() < 0.04 && lastStatus.running && !lastStatus.fail_closed_tripped) {
      spawnPacket();
    }
    requestAnimationFrame(loop);
  }

  layoutFromStatus({});
  loop();

  return {
    setStatus(s) {
      lastStatus = s || {};
      layoutFromStatus(lastStatus);
    },
  };
}
