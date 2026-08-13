#!/usr/bin/env python3
"""Render 1200x630 social / Open Graph card for trenchcoat.jonbailey.xyz (Velvet Collar)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "landing" / "assets" / "og-card.png"
OUT_JPG = ROOT / "landing" / "assets" / "og.jpg"
MKT = ROOT / "assets" / "marketing" / "og-card.png"
W, H = 1200, 630

BG = (10, 11, 20)
PARCHMENT = (232, 224, 213)
MUTED = (154, 147, 136)
SAGE = (107, 143, 122)
GOLD = (201, 162, 39)
GOLD_SOFT = (212, 184, 74)


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    kit = Path.home() / "design-assets" / "fontshare"
    candidates: list[str] = []
    if bold:
        candidates.extend(
            [
                str(kit / "clash-display" / "otf" / "ClashDisplay-Semibold.otf"),
                str(kit / "clash-display" / "otf" / "ClashDisplay-Bold.otf"),
                str(kit / "satoshi" / "otf" / "Satoshi-Bold.otf"),
                r"C:\Windows\Fonts\segoeuib.ttf",
                r"C:\Windows\Fonts\arialbd.ttf",
            ]
        )
    else:
        candidates.extend(
            [
                str(kit / "satoshi" / "otf" / "Satoshi-Medium.otf"),
                str(kit / "satoshi" / "otf" / "Satoshi-Regular.otf"),
                r"C:\Windows\Fonts\segoeui.ttf",
                r"C:\Windows\Fonts\arial.ttf",
            ]
        )
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def main() -> None:
    hero_path = ROOT / "landing" / "assets" / "trench-coat-hero.jpg"
    mark_path = ROOT / "landing" / "assets" / "trench-coat-mark.png"

    img = Image.new("RGB", (W, H), BG)

    if hero_path.exists():
        hero = Image.open(hero_path).convert("RGB")
        scale = max(W / hero.width, H / hero.height)
        hw, hh = int(hero.width * scale), int(hero.height * scale)
        hero = hero.resize((hw, hh), Image.Resampling.LANCZOS)
        cx, cy = hw // 2, hh // 2
        hero = hero.crop((cx - W // 2, cy - H // 2, cx - W // 2 + W, cy - H // 2 + H))
        hero = ImageEnhance.Brightness(hero).enhance(0.55)
        hero = ImageEnhance.Color(hero).enhance(0.85)
        img.paste(hero, (0, 0))

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for x in range(W):
        t = max(0.0, min(1.0, (x - 280) / 520))
        alpha = int(230 * (1.0 - t * 0.92))
        od.line([(x, 0), (x, H)], fill=(10, 11, 20, alpha))
    for y in range(H // 2, H):
        t = (y - H // 2) / (H // 2)
        od.line([(0, y), (W, y)], fill=(10, 11, 20, int(90 * t)))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    if mark_path.exists():
        mark = Image.open(mark_path).convert("RGBA")
        mark = mark.resize((96, 96), Image.Resampling.LANCZOS)
        frame = Image.new("RGBA", (104, 104), (0, 0, 0, 0))
        fd = ImageDraw.Draw(frame)
        fd.rounded_rectangle(
            (0, 0, 103, 103),
            radius=22,
            fill=(22, 24, 36, 230),
            outline=(*GOLD, 160),
            width=1,
        )
        frame.paste(mark, (4, 4), mark)
        img.paste(frame, (56, 56), frame)

    f_tag = _font(22, bold=True)
    f_title = _font(58, bold=True)
    f_sub = _font(26, bold=True)
    f_body = _font(22, bold=False)
    f_foot = _font(18, bold=False)

    x0, y0 = 56, 180
    draw.text((x0, y0), "THE SHADOWS ARE YOUR ALLY", fill=GOLD, font=f_tag)
    draw.text((x0, y0 + 42), "TRENCH COAT", fill=PARCHMENT, font=f_title)
    draw.text((x0, y0 + 118), "v1.1.0  |  VELVET COLLAR", fill=SAGE, font=f_sub)
    draw.text((x0, y0 + 168), "Legal-first multi-hop privacy cloak", fill=PARCHMENT, font=f_body)
    draw.text(
        (x0, y0 + 204),
        "Fail-closed  |  Tor-aware  |  AGPL open source",
        fill=MUTED,
        font=f_body,
    )
    draw.text((x0, H - 48), "trenchcoat.jonbailey.xyz", fill=GOLD_SOFT, font=f_foot)
    draw.rectangle((56, H - 72, 220, H - 70), fill=GOLD)

    img = img.filter(ImageFilter.SMOOTH_MORE)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, format="PNG", optimize=True)
    img.convert("RGB").save(OUT_JPG, format="JPEG", quality=90, optimize=True)
    MKT.parent.mkdir(parents=True, exist_ok=True)
    img.save(MKT, format="PNG", optimize=True)
    print(f"Wrote {OUT}")
    print(f"Wrote {OUT_JPG}")
    print(f"Wrote {MKT}")


if __name__ == "__main__":
    main()
