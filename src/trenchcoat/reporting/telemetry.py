"""Opt-in anonymized chain quality telemetry (Phase 5 — Syndicate).

Default OFF. When enabled, records only aggregate latency/health counters
to a local JSON file — no IPs, no hostnames, no destinations.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from platformdirs import user_data_dir


def telemetry_path() -> Path:
    root = Path(user_data_dir("trench-coat", "trenchcoat"))
    root.mkdir(parents=True, exist_ok=True)
    return root / "telemetry.json"


@dataclass
class TelemetryEvent:
    ts: float
    event: str
    chain_profile: str = ""
    hop_count: int = 0
    healthy_hops: int = 0
    total_latency_ms: float | None = None
    # never store hosts/IPs


@dataclass
class TelemetryStore:
    enabled: bool = False
    install_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    events: list[dict[str, Any]] = field(default_factory=list)
    max_events: int = 200


def load_store() -> TelemetryStore:
    path = telemetry_path()
    if not path.exists():
        return TelemetryStore()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return TelemetryStore(
            enabled=bool(data.get("enabled", False)),
            install_id=str(data.get("install_id") or uuid.uuid4().hex[:16]),
            events=list(data.get("events") or [])[-200:],
            max_events=int(data.get("max_events") or 200),
        )
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return TelemetryStore()


def save_store(store: TelemetryStore) -> Path:
    path = telemetry_path()
    payload = {
        "enabled": store.enabled,
        "install_id": store.install_id,
        "max_events": store.max_events,
        "events": store.events[-store.max_events :],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def set_enabled(enabled: bool) -> TelemetryStore:
    store = load_store()
    store.enabled = enabled
    save_store(store)
    return store


def record(
    event: str,
    *,
    chain_profile: str = "",
    hop_count: int = 0,
    healthy_hops: int = 0,
    total_latency_ms: float | None = None,
) -> None:
    store = load_store()
    if not store.enabled:
        return
    ev = TelemetryEvent(
        ts=time.time(),
        event=event,
        chain_profile=chain_profile,
        hop_count=hop_count,
        healthy_hops=healthy_hops,
        total_latency_ms=total_latency_ms,
    )
    store.events.append(asdict(ev))
    store.events = store.events[-store.max_events :]
    save_store(store)


def summary() -> dict[str, Any]:
    store = load_store()
    n = len(store.events)
    latencies = [
        e["total_latency_ms"]
        for e in store.events
        if isinstance(e.get("total_latency_ms"), (int, float))
    ]
    avg = sum(latencies) / len(latencies) if latencies else None
    return {
        "enabled": store.enabled,
        "install_id": store.install_id,
        "events": n,
        "avg_latency_ms": round(avg, 1) if avg is not None else None,
        "path": str(telemetry_path()),
    }
