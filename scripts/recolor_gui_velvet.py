#!/usr/bin/env python3
"""Recolor neon Command Nexus screenshot into Velvet Collar palette (HSV-based)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "assets" / "masters" / "velvet-collar-v1.1" / "gui-nexus-neon-marketing.png"
FALLBACKS = [
    ROOT / "assets" / "masters" / "velvet-collar-v1.1" / "gui-nexus-neon-original.png",
    ROOT / "assets" / "marketing" / "trench-coat-gui-screenshot.png",
]
OUTS = [
    ROOT / "landing" / "assets" / "trench-coat-gui-online.png",
    ROOT / "assets" / "marketing" / "trench-coat-gui-online.png",
    ROOT / "assets" / "screenshots" / "gui-nexus.png",
    ROOT / "assets" / "masters" / "velvet-collar-v1.1" / "gui-nexus-velvet.png",
]


def _src() -> Path:
    for p in [SRC, *FALLBACKS]:
        if p.is_file():
            return p
    raise SystemExit("No neon GUI source found")


def rgb_to_hsv(arr: np.ndarray) -> np.ndarray:
    """arr float RGB 0-1 -> HSV (H 0-360, S 0-1, V 0-1)."""
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    mx = np.maximum(np.maximum(r, g), b)
    mn = np.minimum(np.minimum(r, g), b)
    df = mx - mn
    h = np.zeros_like(mx)
    mask = df > 1e-6
    rmax = mask & (mx == r)
    gmax = mask & (mx == g)
    bmax = mask & (mx == b)
    h[rmax] = (60 * ((g[rmax] - b[rmax]) / df[rmax]) + 360) % 360
    h[gmax] = (60 * ((b[gmax] - r[gmax]) / df[gmax]) + 120) % 360
    h[bmax] = (60 * ((r[bmax] - g[bmax]) / df[bmax]) + 240) % 360
    s = np.divide(df, mx, out=np.zeros_like(mx), where=mx > 1e-6)
    v = mx
    return np.stack([h, s, v], axis=-1)


def hsv_to_rgb(hsv: np.ndarray) -> np.ndarray:
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    c = v * s
    x = c * (1 - np.abs((h / 60) % 2 - 1))
    m = v - c
    z = np.zeros_like(h)
    rgb = np.zeros((*h.shape, 3), dtype=np.float32)
    # sectors
    conds = [
        (h < 60, (c, x, z)),
        ((h >= 60) & (h < 120), (x, c, z)),
        ((h >= 120) & (h < 180), (z, c, x)),
        ((h >= 180) & (h < 240), (z, x, c)),
        ((h >= 240) & (h < 300), (x, z, c)),
        (h >= 300, (c, z, x)),
    ]
    for cond, (rr, gg, bb) in conds:
        rgb[cond, 0] = rr[cond]
        rgb[cond, 1] = gg[cond]
        rgb[cond, 2] = bb[cond]
    rgb[..., 0] += m
    rgb[..., 1] += m
    rgb[..., 2] += m
    return np.clip(rgb, 0, 1)


def recolor(arr_u8: np.ndarray) -> np.ndarray:
    arr = arr_u8.astype(np.float32) / 255.0
    hsv = rgb_to_hsv(arr)
    h, s, v = hsv[..., 0].copy(), hsv[..., 1].copy(), hsv[..., 2].copy()

    # Neon green / cyan family (roughly 120-180, high sat)
    green = (s > 0.2) & (h >= 100) & (h <= 185)
    # Map to sage-ish hue ~145-155 with moderated sat
    h[green] = 145 + (h[green] - 140) * 0.15
    s[green] = np.clip(s[green] * 0.45 + 0.12, 0.15, 0.55)
    # lift dark greens slightly for readability
    v[green] = np.clip(v[green] * 0.92 + 0.05, 0, 1)

    # Magenta / pink / hot purple path (300-360 and 0-20, high sat) + purple 260-300
    magenta = (s > 0.18) & (((h >= 280) & (h <= 360)) | (h <= 25))
    purple = (s > 0.18) & (h >= 250) & (h < 280)
    # Magenta -> gold (~42)
    h[magenta] = 42 + (h[magenta] % 40) * 0.05
    s[magenta] = np.clip(s[magenta] * 0.55 + 0.2, 0.25, 0.75)
    v[magenta] = np.clip(v[magenta] * 0.95 + 0.04, 0, 1)
    # Cool purple borders -> muted slate-blue-gold mix (~210 with low sat) or soft gold
    # Prefer soft gold for UI chrome consistency
    h[purple] = 48
    s[purple] = np.clip(s[purple] * 0.35 + 0.1, 0.12, 0.45)
    v[purple] = np.clip(v[purple] * 0.9 + 0.05, 0, 1)

    # Blue-ish neon residual (185-250 high sat)
    blueish = (s > 0.25) & (h > 185) & (h < 250)
    h[blueish] = 150
    s[blueish] = np.clip(s[blueish] * 0.3, 0.1, 0.4)

    # Very dark backgrounds: push toward indigo (low V, low S)
    dark = v < 0.12
    s[dark] = np.clip(s[dark] * 0.3, 0, 0.15)
    # slight blue-indigo hue for void
    h[dark] = 230
    v[dark] = np.clip(v[dark] * 0.9 + 0.02, 0, 0.14)

    # Mid desaturated panels warm slightly
    mid = (v >= 0.12) & (v < 0.45) & (s < 0.15)
    h[mid] = 40
    s[mid] = np.clip(s[mid] + 0.04, 0, 0.12)

    out = hsv_to_rgb(np.stack([h, s, v], axis=-1))
    out_u8 = (out * 255).astype(np.uint8)
    im = Image.fromarray(out_u8, mode="RGB")
    # Soften neon harshness
    im = ImageEnhance.Color(im).enhance(0.92)
    im = ImageEnhance.Contrast(im).enhance(1.04)
    return np.asarray(im)


def main() -> None:
    src = _src()
    print(f"source: {src} ({src.stat().st_size} bytes)")
    im = Image.open(src).convert("RGB")
    out = Image.fromarray(recolor(np.asarray(im)), mode="RGB")
    for dest in OUTS:
        dest.parent.mkdir(parents=True, exist_ok=True)
        out.save(dest, format="PNG", optimize=True)
        print(f"wrote {dest} ({dest.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
