#!/usr/bin/env python3
"""Render Trench Coat how-the-cloak-works infographic (Velvet Collar, exact text)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
W, H = 1600, 1100

# Velvet Collar palette
BG = (10, 11, 20)
BG2 = (18, 20, 31)
PANEL = (22, 24, 36)
PANEL2 = (28, 30, 44)
BORDER = (70, 66, 58)
SAGE = (107, 143, 122)
SAGE_SOFT = (138, 168, 150)
GOLD = (201, 162, 39)
GOLD_SOFT = (212, 184, 74)
PARCHMENT = (232, 224, 213)
MUTED = (154, 147, 136)
DANGER = (196, 92, 106)
INK = (8, 9, 14)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    kit = Path.home() / "design-assets" / "fontshare"
    candidates: list[str] = []
    if bold:
        candidates += [
            str(kit / "clash-display" / "otf" / "ClashDisplay-Semibold.otf"),
            str(kit / "clash-display" / "otf" / "ClashDisplay-Bold.otf"),
            str(kit / "satoshi" / "otf" / "Satoshi-Bold.otf"),
            r"C:\Windows\Fonts\segoeuib.ttf",
            r"C:\Windows\Fonts\arialbd.ttf",
        ]
    else:
        candidates += [
            str(kit / "satoshi" / "otf" / "Satoshi-Medium.otf"),
            str(kit / "satoshi" / "otf" / "Satoshi-Regular.otf"),
            r"C:\Windows\Fonts\segoeui.ttf",
            r"C:\Windows\Fonts\arial.ttf",
        ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def rounded(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    fill: tuple[int, int, int],
    radius: int = 18,
    outline: tuple[int, int, int] | None = None,
    width: int = 1,
) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def text_center(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float],
    text: str,
    fnt: ImageFont.ImageFont,
    fill: tuple[int, int, int],
) -> None:
    bbox = draw.textbbox((0, 0), text, font=fnt)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((xy[0] - tw / 2, xy[1] - th / 2), text, font=fnt, fill=fill)


def wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    fnt: ImageFont.ImageFont,
    max_width: int,
) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur = ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=fnt) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def main() -> None:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # soft vignette / fog wash
    wash = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    wd = ImageDraw.Draw(wash)
    for i in range(40):
        alpha = int(10 + i * 1.2)
        wd.ellipse(
            (-200 + i * 8, -120 + i * 6, W + 200 - i * 8, H // 2 + i * 10),
            fill=(107, 143, 122, alpha // 3),
        )
    for i in range(30):
        wd.ellipse(
            (W // 3 + i * 10, H // 3 + i * 8, W + 100 - i * 6, H + 80 - i * 4),
            fill=(201, 162, 39, 4),
        )
    img = Image.alpha_composite(img.convert("RGBA"), wash).convert("RGB")
    d = ImageDraw.Draw(img)

    # subtle rain ticks
    for i in range(70):
        x = (i * 53) % W
        y0 = (i * 71) % H
        d.line((x, y0, x - 2, y0 + 16), fill=(40, 44, 58), width=1)

    title = font(52, bold=True)
    sub = font(20, bold=True)
    h2 = font(22, bold=True)
    body = font(18)
    small = font(15)
    step_n = font(20, bold=True)

    text_center(d, (W // 2, 48), "HOW THE CLOAK WORKS", title, PARCHMENT)
    text_center(d, (W // 2, 96), "THE SHADOWS ARE YOUR ALLY  |  VELVET COLLAR 1.1", sub, GOLD)
    text_center(
        d,
        (W // 2, 130),
        "Legal-first multi-hop privacy  |  local SOCKS entry  |  fail-closed by default",
        small,
        MUTED,
    )

    # Five sequential steps across a pathway
    steps = [
        ("1", "Apps", "Point apps at the local cloak entry"),
        ("2", "Local entry", "socks5://127.0.0.1:1080"),
        ("3", "Nested hops", "VPN SOCKS, Tor, self-hosted relays"),
        ("4", "Egress", "Exit identity from the last hop"),
        ("5", "Fail-closed", "Dead chain refuses CONNECT"),
    ]

    # pathway bar
    y_path = 280
    d.rounded_rectangle((80, y_path - 6, W - 80, y_path + 6), radius=6, fill=(32, 36, 48))
    d.rounded_rectangle((80, y_path - 6, W - 80, y_path + 6), radius=6, outline=BORDER, width=1)

    card_w = 250
    gap = (W - 160 - card_w * 5) / 4
    x0 = 80
    cards_y = 200

    for i, (num, label, detail) in enumerate(steps):
        cx = x0 + i * (card_w + gap) + card_w / 2
        # node on path
        d.ellipse((cx - 12, y_path - 12, cx + 12, y_path + 12), fill=GOLD if i == 4 else SAGE)
        d.ellipse((cx - 12, y_path - 12, cx + 12, y_path + 12), outline=PARCHMENT, width=1)

        # card above or below alternating
        cy = cards_y if i % 2 == 0 else 340
        box = (int(cx - card_w / 2), cy, int(cx + card_w / 2), cy + 120)
        rounded(d, box, PANEL, radius=16, outline=BORDER, width=1)
        # number badge
        d.ellipse((box[0] + 16, cy + 18, box[0] + 48, cy + 50), fill=GOLD)
        text_center(d, (box[0] + 32, cy + 34), num, step_n, INK)
        d.text((box[0] + 58, cy + 22), label, font=h2, fill=PARCHMENT)
        # detail wrapped
        lines = wrap_text(d, detail, small, card_w - 36)
        ty = cy + 58
        for ln in lines:
            d.text((box[0] + 18, ty), ln, font=small, fill=MUTED)
            ty += 20

        # connector from card to node
        if i % 2 == 0:
            d.line((cx, cy + 120, cx, y_path - 12), fill=BORDER, width=1)
        else:
            d.line((cx, cy, cx, y_path + 12), fill=BORDER, width=1)

    # Detail panels bottom
    panels = [
        (
            "What observers see",
            [
                "LAN / ISP: first hop only",
                "Intermediate hop: adjacent links",
                "Website: exit IP + app fingerprint",
                "Endpoint malware: everything (out of scope)",
            ],
        ),
        (
            "Verify the coat",
            [
                "trench doctor",
                "trench up --accept-legal --wait-tor 60",
                "trench check-ip   (expect IsTor: true)",
                "trench gui  ->  http://127.0.0.1:8742",
            ],
        ),
        (
            "Not claimed",
            [
                "Not a Tor Browser replacement",
                "Not a crime toolkit",
                "Not nation-state proof",
                "Soft mode only cloaks SOCKS apps",
            ],
        ),
    ]

    py = 520
    pw = 460
    pg = 30
    px0 = 80
    for i, (ptitle, bullets) in enumerate(panels):
        x = px0 + i * (pw + pg)
        rounded(d, (x, py, x + pw, py + 280), PANEL2, radius=18, outline=BORDER, width=1)
        d.text((x + 24, py + 22), ptitle.upper(), font=h2, fill=GOLD)
        d.line((x + 24, py + 58, x + pw - 24, py + 58), fill=BORDER, width=1)
        ty = py + 78
        for b in bullets:
            d.ellipse((x + 28, ty + 6, x + 36, ty + 14), fill=SAGE if i < 2 else DANGER)
            d.text((x + 48, ty), b, font=body, fill=PARCHMENT if i < 2 else MUTED)
            ty += 42

    # footer
    text_center(
        d,
        (W // 2, H - 48),
        "Trench Coat  |  Pitchfork-and-Torch  |  AGPL-3.0  |  Not affiliated with the Tor Project",
        small,
        MUTED,
    )
    text_center(
        d,
        (W // 2, H - 24),
        "trenchcoat.jonbailey.xyz",
        small,
        SAGE_SOFT,
    )

    # soft paper grain-ish blur edge
    img = img.filter(ImageFilter.SMOOTH)

    outs = [
        ROOT / "landing" / "assets" / "trench-coat-infographic.png",
        ROOT / "landing" / "assets" / "trench-coat-infographic.jpg",
        ROOT / "assets" / "screenshots" / "trench-coat-infographic.png",
        ROOT / "assets" / "marketing" / "TRENCH-COAT-INFOGRAPHIC.png",
        ROOT / "assets" / "masters" / "velvet-collar-v1.1" / "how-cloak-works-infographic.png",
    ]
    for out in outs:
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.suffix.lower() in {".jpg", ".jpeg"}:
            img.convert("RGB").save(out, format="JPEG", quality=92, optimize=True)
        else:
            img.save(out, format="PNG", optimize=True)
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
