#!/usr/bin/env python3
"""Render 1200x630 social / Open Graph card for trenchcoat.jonbailey.xyz."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "landing" / "assets" / "og-card.png"
MKT = ROOT / "assets" / "marketing" / "og-card.png"
W, H = 1200, 630


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for name in (
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/seguisb.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def main() -> None:
    hero_path = ROOT / "landing" / "assets" / "trench-coat-hero.jpg"
    gui_path = ROOT / "landing" / "assets" / "trench-coat-gui-online.png"

    img = Image.new("RGB", (W, H), (5, 5, 10))
    left_w = 700
    hero = Image.open(hero_path).convert("RGB")
    scale = max(left_w / hero.width, H / hero.height)
    hw, hh = int(hero.width * scale), int(hero.height * scale)
    hero = hero.resize((hw, hh), Image.Resampling.LANCZOS)
    cx, cy = hw // 2, hh // 2
    hero = hero.crop((cx - left_w // 2, cy - H // 2, cx - left_w // 2 + left_w, cy - H // 2 + H))
    img.paste(hero, (0, 0))

    panel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(panel)
    for x in range(W):
        t = max(0.0, min(1.0, (x - 420) / 280))
        pd.line([(x, 0), (x, H)], fill=(8, 6, 14, int(240 * t)))
    img = Image.alpha_composite(img.convert("RGBA"), panel).convert("RGB")
    draw = ImageDraw.Draw(img)

    if gui_path.exists():
        gui = Image.open(gui_path).convert("RGB")
        gw, gh = 480, 310
        gscale = max(gw / gui.width, gh / gui.height)
        g2 = gui.resize((int(gui.width * gscale), int(gui.height * gscale)), Image.Resampling.LANCZOS)
        g2 = g2.crop((0, 0, gw, gh))
        frame = Image.new("RGB", (gw + 8, gh + 8), (0, 255, 159))
        frame.paste(g2, (4, 4))
        img.paste(frame, (W - gw - 48, 140))

    f_tag, f_title, f_sub, f_body, f_foot = (
        _font(22),
        _font(54),
        _font(28),
        _font(22),
        _font(18),
    )
    x0, y0 = 56, 72
    draw.text((x0, y0), "THE SHADOWS ARE YOUR ALLY", fill=(255, 0, 170), font=f_tag)
    draw.text((x0, y0 + 48), "TRENCH COAT", fill=(0, 255, 159), font=f_title)
    draw.text((x0, y0 + 120), "v1.0  ·  NEON COLLAR", fill=(123, 44, 191), font=f_sub)
    draw.text((x0, y0 + 170), "Legal-first multi-hop privacy cloak", fill=(200, 245, 224), font=f_body)
    draw.text(
        (x0, y0 + 205),
        "Fail-closed  ·  Tor-aware  ·  AGPL open source",
        fill=(90, 122, 106),
        font=f_body,
    )
    draw.rectangle([0, H - 52, W, H], fill=(8, 8, 16))
    draw.text(
        (56, H - 36),
        "trenchcoat.jonbailey.xyz  ·  Pitchfork-and-Torch",
        fill=(0, 255, 159),
        font=f_foot,
    )
    draw.text((W - 280, H - 36), "socks5://127.0.0.1:1080", fill=(255, 0, 170), font=f_foot)
    draw.rectangle([0, 0, W, 3], fill=(0, 255, 159))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    MKT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, "PNG", optimize=True)
    img.save(MKT, "PNG", optimize=True)
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes) {img.size}")


if __name__ == "__main__":
    main()
