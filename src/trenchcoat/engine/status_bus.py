"""Cross-process status bus — file-backed so `trench gui` can see `trench up`."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from trenchcoat.config.loader import data_dir


def status_path() -> Path:
    return data_dir() / "runtime_status.json"


def write_status(payload: dict[str, Any]) -> Path:
    path = status_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {**payload, "updated_at": time.time()}
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def read_status(max_age_seconds: float = 90.0) -> dict[str, Any] | None:
    path = status_path()
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None
    updated = float(data.get("updated_at") or 0)
    if max_age_seconds and (time.time() - updated) > max_age_seconds:
        data["stale"] = True
    return data


def clear_status() -> None:
    path = status_path()
    if path.exists():
        try:
            path.unlink()
        except OSError:
            pass
