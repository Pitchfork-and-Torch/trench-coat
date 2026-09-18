/* Trench Coat landing - Velvet Collar ambient + reveals */
(function () {
  "use strict";

  var reduce =
    window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* Scroll reveals */
  var panels = document.querySelectorAll(".panel.reveal");
  if (panels.length && "IntersectionObserver" in window && !reduce) {
    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            io.unobserve(entry.target);
          }
        });
      },
      { rootMargin: "0px 0px -8% 0px", threshold: 0.12 }
    );
    panels.forEach(function (el) {
      io.observe(el);
    });
  } else {
    panels.forEach(function (el) {
      el.classList.add("is-visible");
    });
  }

  /* Soft rain canvas */
  if (reduce) return;

  var canvas = document.getElementById("rain-canvas");
  if (!canvas || !canvas.getContext) return;

  var ctx = canvas.getContext("2d");
  var drops = [];
  var dpr = Math.min(window.devicePixelRatio || 1, 2);
  var w = 0;
  var h = 0;
  var running = true;
  var last = 0;

  function resize() {
    w = window.innerWidth;
    h = window.innerHeight;
    canvas.width = Math.floor(w * dpr);
    canvas.height = Math.floor(h * dpr);
    canvas.style.width = w + "px";
    canvas.style.height = h + "px";
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    var count = Math.min(90, Math.floor(w / 18));
    drops = [];
    for (var i = 0; i < count; i++) {
      drops.push({
        x: Math.random() * w,
        y: Math.random() * h,
        len: 8 + Math.random() * 14,
        speed: 2.2 + Math.random() * 3.2,
        alpha: 0.08 + Math.random() * 0.14,
      });
    }
  }

  function frame(ts) {
    if (!running) return;
    if (ts - last < 32) {
      requestAnimationFrame(frame);
      return;
    }
    last = ts;
    ctx.clearRect(0, 0, w, h);
    ctx.lineWidth = 1;
    for (var i = 0; i < drops.length; i++) {
      var d = drops[i];
      ctx.strokeStyle = "rgba(200, 210, 230," + d.alpha + ")";
      ctx.beginPath();
      ctx.moveTo(d.x, d.y);
      ctx.lineTo(d.x - 1.2, d.y + d.len);
      ctx.stroke();
      d.y += d.speed;
      d.x -= 0.35;
      if (d.y > h + 20) {
        d.y = -20;
        d.x = Math.random() * w;
      }
    }
    requestAnimationFrame(frame);
  }

  function onVis() {
    running = document.visibilityState !== "hidden";
    if (running) {
      last = 0;
      requestAnimationFrame(frame);
    }
  }

  window.addEventListener("resize", resize, { passive: true });
  document.addEventListener("visibilitychange", onVis);
  resize();
  requestAnimationFrame(frame);
})();
