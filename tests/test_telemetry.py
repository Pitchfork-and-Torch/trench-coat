"""Telemetry opt-in local store tests."""

from __future__ import annotations

from trenchcoat.reporting import telemetry


def test_telemetry_default_off(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(telemetry, "telemetry_path", lambda: tmp_path / "telemetry.json")
    store = telemetry.load_store()
    assert store.enabled is False
    telemetry.record("test", hop_count=1)
    # still off — no event
    store = telemetry.load_store()
    assert store.events == []

    telemetry.set_enabled(True)
    telemetry.record("test", hop_count=2, healthy_hops=1, total_latency_ms=42.0)
    store = telemetry.load_store()
    assert store.enabled is True
    assert len(store.events) == 1
    assert "host" not in store.events[0]
    assert store.events[0]["total_latency_ms"] == 42.0
    s = telemetry.summary()
    assert s["events"] == 1
