#!/usr/bin/env python3
"""Render Trench Coat explainer infographic (exact text, cyber-noir)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1600, 2200
BG = (5, 5, 10)
PANEL = (12, 12, 20)
GREEN = (0, 255, 159)
MAGENTA = (255, 0, 170)
PURPLE = (123, 44, 191)
TEXT = (200, 245, 224)
DIM = (90, 122, 106)
WHITE = (240, 248, 255)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\consolab.ttf" if bold else r"C:\Windows\Fonts\consola.ttf",
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def rounded(draw: ImageDraw.ImageDraw, box, fill, radius=18, outline=None, width=2):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def text_center(draw, xy, text, fnt, fill):
    bbox = draw.textbbox((0, 0), text, font=fnt)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((xy[0] - tw / 2, xy[1] - th / 2), text, font=fnt, fill=fill)


def main() -> Path:
    out = Path.home() / "Desktop" / "TRENCH-COAT-INFOGRAPHIC.png"
    out_repo = Path(__file__).resolve().parents[1] / "assets" / "screenshots" / "trench-coat-infographic.png"
    out_repo.parent.mkdir(parents=True, exist_ok=True)

    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # subtle vignette bars + rain (RGB only)
    for i in range(90):
        x = (i * 41) % W
        y0r = (i * 59) % H
        d.line((x, y0r, x + 3, y0r + 22), fill=(20, 40, 32), width=1)

    title_f = font(64, bold=True)
    sub_f = font(22, bold=True)
    h2 = font(28, bold=True)
    body = font(20)
    small = font(16)
    mono = font(18, bold=True)

    # header
    text_center(d, (W // 2, 70), "TRENCH COAT", title_f, GREEN)
    text_center(d, (W // 2, 130), "THE SHADOWS ARE YOUR ALLY", sub_f, MAGENTA)
    text_center(
        d,
        (W // 2, 175),
        "Legal-first multi-hop privacy cloak  ·  open source  ·  v0.3",
        small,
        DIM,
    )

    # what it does panel
    y0 = 220
    rounded(d, (60, y0, W - 60, y0 + 200), PANEL, outline=GREEN, width=2)
    d.text((90, y0 + 25), "WHAT IT DOES", font=h2, fill=MAGENTA)
    blurb = (
        "Trench Coat routes your apps through a local SOCKS entry that chains privacy hops\n"
        "(Tor, VPN SOCKS, self-hosted relays, and more). Observers on your network see\n"
        "encrypted traffic to the first hop — not your destinations. Fail-closed by design:\n"
        "if the chain dies, the cloak refuses to leak you onto clearnet."
    )
    d.multiline_text((90, y0 + 75), blurb, font=body, fill=TEXT, spacing=8)

    # flow diagram
    y1 = 460
    rounded(d, (60, y1, W - 60, y1 + 320), PANEL, outline=PURPLE, width=2)
    d.text((90, y1 + 20), "HOW TRAFFIC FLOWS", font=h2, fill=GREEN)

    boxes = [
        (120, y1 + 120, "YOUR\nAPPS"),
        (420, y1 + 120, "TRENCH\nENTRY\n:1080"),
        (720, y1 + 120, "HOPS\nVPN · VPS\n· TOR"),
        (1020, y1 + 120, "OPEN\nNET"),
        (1320, y1 + 120, "EXIT\nIDENTITY"),
    ]
    for x, y, label in boxes:
        rounded(d, (x, y, x + 180, y + 140), (8, 14, 18), outline=GREEN, width=2)
        lines = label.split("\n")
        for i, line in enumerate(lines):
            text_center(d, (x + 90, y + 40 + i * 28), line, mono, GREEN if i == 0 else TEXT)

    # arrows
    for x in (300, 600, 900, 1200):
        d.polygon(
            [(x + 20, y1 + 185), (x + 50, y1 + 170), (x + 50, y1 + 200)],
            fill=MAGENTA,
        )
        d.line((x - 10, y1 + 185, x + 25, y1 + 185), fill=MAGENTA, width=3)

    d.text(
        (90, y1 + 275),
        "Example: Browser → socks5://127.0.0.1:1080 → Tor → website  (IsTor: true)",
        font=small,
        fill=DIM,
    )

    # features grid
    y2 = 820
    d.text((90, y2), "CORE CAPABILITIES", font=h2, fill=MAGENTA)
    features = [
        ("MULTI-HOP CHAINS", "Stack 1–10+ hops: Tor, SOCKS5/HTTP,\nresidential bridges, self-hosted VPS."),
        ("AUTO TOR DETECT", "Finds local Tor on 9050/9150 and\nbinds hops automatically."),
        ("FAIL-CLOSED", "No live hops → no silent clearnet.\nSoft kill-switch armed by default."),
        ("CHECK-IP", "Prove egress: IsTor + public IP via\ncheck.torproject.org."),
        ("PROFILES", "Casual Shadow · Ghost · Journalist\nWhistleblower · Paranoid."),
        ("COMMAND NEXUS", "Cyberpunk web GUI + local API.\nCity-map hop visualization."),
        ("DOSSIERS", "Encrypted-ready local session logs\nexport as classified HTML."),
        ("GHOST CONTINUUM", "Optional 8th plane: cloak health\nfeeds the immune fabric."),
    ]
    cols, rows = 2, 4
    card_w, card_h = 700, 150
    gap_x, gap_y = 40, 24
    start_x, start_y = 80, y2 + 50
    for i, (title, desc) in enumerate(features):
        col, row = i % cols, i // cols
        x = start_x + col * (card_w + gap_x)
        y = start_y + row * (card_h + gap_y)
        rounded(d, (x, y, x + card_w, y + card_h), PANEL, outline=(0, 255, 159, 80), width=2)
        d.text((x + 24, y + 22), title, font=mono, fill=GREEN)
        d.multiline_text((x + 24, y + 60), desc, font=body, fill=TEXT, spacing=6)

    # legal
    y3 = 1680
    rounded(d, (60, y3, W - 60, y3 + 160), (20, 8, 16), outline=MAGENTA, width=2)
    d.text((90, y3 + 25), "LEGAL-FIRST  ·  NOT A CRIME TOOLKIT", font=h2, fill=MAGENTA)
    d.multiline_text(
        (90, y3 + 75),
        "For privacy, censorship resistance, and opsec — not fraud, harassment, or crime.\n"
        "You own compliance with the laws of your jurisdiction.  trench legal",
        font=body,
        fill=TEXT,
        spacing=6,
    )

    # footer
    y4 = 1880
    rounded(d, (60, y4, W - 60, y4 + 220), PANEL, outline=PURPLE, width=2)
    d.text((90, y4 + 25), "GET STARTED", font=h2, fill=GREEN)
    steps = (
        "1. git clone https://github.com/Pitchfork-and-Torch/trench-coat.git\n"
        "2. pip install -e .   ·   scripts/start-tor.ps1 (or Tor Browser)\n"
        "3. trench up --accept-legal --wait-tor 60\n"
        "4. Point apps to socks5://127.0.0.1:1080   ·   trench check-ip"
    )
    d.multiline_text((90, y4 + 75), steps, font=mono, fill=TEXT, spacing=10)

    text_center(d, (W // 2, H - 40), "github.com/Pitchfork-and-Torch/trench-coat  ·  AGPL-3.0", small, DIM)

    img.save(out, "PNG", optimize=True)
    img.save(out_repo, "PNG", optimize=True)
    print(out)
    print(out_repo)
    return out


if __name__ == "__main__":
    main()
