"""Community chain templates (Phase 5 — Syndicate).

YAML templates ship under configs/templates/ and can be listed/imported
without auto-enabling network traffic.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from trenchcoat.config.models import ChainConfig


def templates_dir() -> Path:
    """Resolve configs/templates from repo checkout or CWD."""
    # .../src/trenchcoat/config/templates.py → repo root is parents[3]
    candidates = [
        Path(__file__).resolve().parents[3] / "configs" / "templates",
        Path.cwd() / "configs" / "templates",
    ]
    for path in candidates:
        if path.is_dir():
            return path
    return candidates[0]


def list_templates() -> list[dict[str, Any]]:
    root = templates_dir()
    if not root.is_dir():
        return []
    out: list[dict[str, Any]] = []
    for path in sorted(root.glob("*.yaml")):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError):
            continue
        meta = data.get("meta") or {}
        out.append(
            {
                "id": path.stem,
                "path": str(path),
                "title": meta.get("title") or path.stem,
                "author": meta.get("author") or "community",
                "description": meta.get("description") or "",
                "tags": meta.get("tags") or [],
            }
        )
    return out


def load_template(template_id: str) -> ChainConfig:
    path = templates_dir() / f"{template_id}.yaml"
    if not path.is_file():
        # allow bare path stem without .yaml already
        candidates = list(templates_dir().glob(f"{template_id}*"))
        if not candidates:
            raise FileNotFoundError(f"Template not found: {template_id}")
        path = candidates[0]
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    chain_data = data.get("chain") or data
    # strip meta if nested at top
    if "meta" in chain_data:
        chain_data = {k: v for k, v in chain_data.items() if k != "meta"}
    return ChainConfig.model_validate(chain_data)
