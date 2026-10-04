"""Companion popup must not call a down or pending status Cloaked."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
LABEL = ROOT / "browser_extension" / "status-label.js"


def _label(payload: dict) -> dict:
    node = shutil.which("node")
    if not node:
        pytest.skip("node not on PATH")
    script = (
        "const m = require(process.argv[1]);"
        "const payload = JSON.parse(process.argv[2]);"
        "process.stdout.write(JSON.stringify(m.companionStatus(payload)));"
    )
    result = subprocess.run(
        [node, "-e", script, str(LABEL), json.dumps(payload)],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def test_running_healthy_is_cloaked() -> None:
    view = _label({"running": True, "listen": "127.0.0.1:1080"})
    assert view["label"].startswith("Cloaked")
    assert view["proxyOk"] is True
    assert view["port"] == 1080


def test_pending_is_not_cloaked() -> None:
    view = _label({"running": False, "pending": True})
    assert "Pending" in view["label"]
    assert "Cloaked" not in view["label"]
    assert view["proxyOk"] is False


def test_stale_is_not_cloaked() -> None:
    view = _label({"running": False, "stale": True})
    assert view["label"].startswith("Stale")
    assert view["proxyOk"] is False


def test_port_open_without_owner_is_not_a_cloak() -> None:
    view = _label({"running": False, "listen_port_open": True, "listen": "127.0.0.1:1080"})
    assert view["label"].startswith("Port open")
    assert "Cloaked" not in view["label"]
    assert view["proxyOk"] is False


def test_degraded_hop_is_not_called_cloaked() -> None:
    view = _label(
        {
            "running": True,
            "listen": "127.0.0.1:1080",
            "snapshot": {"healthy": False, "hops": [{"health": "degraded"}]},
        }
    )
    assert view["label"].startswith("Degraded")
    assert "Cloaked" not in view["label"]
    assert view["proxyOk"] is True


def test_dead_hop_does_not_arm_proxy() -> None:
    view = _label(
        {
            "running": True,
            "listen": "127.0.0.1:9050",
            "snapshot": {"hops": [{"health": "dead"}]},
        }
    )
    assert "Not cloaked" in view["label"]
    assert view["proxyOk"] is False
    assert view["port"] == 9050


def test_offline_when_api_missing() -> None:
    view = _label({})
    assert "offline" in view["label"]
    assert view["proxyOk"] is False
