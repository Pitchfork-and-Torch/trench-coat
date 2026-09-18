"""Scan for residual mojibake sequences. Exit 1 if any found."""
from __future__ import annotations

import sys
from pathlib import Path

SKIP = {
    ".git",
    ".venv",
    "__pycache__",
    ".wrangler",
    "node_modules",
    ".pytest_cache",
    ".ruff_cache",
    ".tor-data",
    ".shot-tools",
    "egg-info",
}
EXT = {
    ".md",
    ".txt",
    ".html",
    ".py",
    ".js",
    ".css",
    ".yml",
    ".yaml",
    ".toml",
    ".json",
    ".ps1",
    ".sh",
    ".xml",
}
# Built from codepoints so this file never contains mojibake itself
NEEDLES = [
    "\u00e2\u0153",  # common âœ prefix when still double-wrong; also catch via explicit:
]
# Explicit broken sequences as UTF-8 misreads of common symbols
NEEDLES = [
    bytes([0xE2, 0x80, 0x94]).decode("latin-1"),  # em dash mojibake â€”
    bytes([0xE2, 0x9C, 0x85]).decode("latin-1"),  # checkmark mojibake âœ…
    bytes([0xE2, 0x96, 0x91]).decode("latin-1"),  # block â–‘
    bytes([0xE2, 0x94, 0x80]).decode("latin-1"),  # box â”€
    bytes([0xE2, 0x86, 0x92]).decode("latin-1"),  # arrow â†’
    "\ufffd",
]


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    bad: list[str] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if any(s in p.parts for s in SKIP):
            continue
        if p.name == "check_mojibake.py":
            continue
        if p.suffix.lower() not in EXT:
            continue
        if p.stat().st_size > 5_000_000:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            continue
        if any(n in text for n in NEEDLES):
            bad.append(str(p.relative_to(root)))
    if bad:
        print("MOJIBAKE residual:")
        for b in bad:
            print(" ", b)
        return 1
    print("mojibake clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
