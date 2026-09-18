"""Circuit Desk control API: templates, chain PUT, pid-owned Engage/Disengage."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time

import pytest
from fastapi.testclient import TestClient

from trenchcoat.api.server import create_app
from trenchcoat.config.loader import load_config, save_config
from trenchcoat.config.models import ChainConfig, ChainPolicy, HopConfig, HopType, ProfileName
from trenchcoat.engine.status_bus import claim_owner, owner_alive, release_owner


@pytest.fixture
def client(isolated):
    return TestClient(create_app())


def test_templates_have_no_home_paths(client):
    r = client.get("/api/templates")
    assert r.status_code == 200
    body = r.text.lower()
    assert "users\\knock" not in body
    assert "c:\\users" not in body
    assert "/users/knock" not in body
    rows = r.json()
    assert isinstance(rows, list)
    assert rows
    for item in rows:
        assert "path" not in item
        assert item.get("id")
        assert item.get("title")


def test_put_empty_fail_closed_rejected(client):
    r = client.put(
        "/api/chain",
        json={"name": "custom-desk", "hops": [], "policy": {"min_hops": 1, "fail_closed": True}},
    )
    assert r.status_code == 400
    assert "hop" in r.json()["detail"].lower()


def test_put_valid_chain_and_get(client):
    r = client.put(
        "/api/chain",
        json={
            "name": "custom-desk",
            "description": "Circuit Desk test",
            "hops": [
                {
                    "id": "tor-local",
                    "type": "tor",
                    "host": "127.0.0.1",
                    "port": 9050,
                    "label": "Tor",
                    "enabled": True,
                }
            ],
            "policy": {"min_hops": 1, "fail_closed": True},
        },
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["ok"] is True
    assert data["name"] == "custom-desk"
    assert data["can_engage"] is True
    assert data["hops"][0]["id"] == "tor-local"
    assert "password" not in data["hops"][0]
    assert data["hops"][0]["has_auth"] is False

    got = client.get("/api/chain")
    assert got.status_code == 200
    assert got.json()["name"] == "custom-desk"
    assert got.json()["enabled_count"] == 1


def test_import_template(client):
    r = client.post("/api/templates/casual-tor/import")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["ok"] is True
    assert data["hops"]
    assert data["can_engage"] is True


def test_cloak_up_conflict_when_owned(client):
    client.put(
        "/api/chain",
        json={
            "name": "custom-desk",
            "hops": [
                {"id": "tor-local", "type": "tor", "host": "127.0.0.1", "port": 9050, "enabled": True}
            ],
        },
    )
    claim_owner(os.getpid())
    r = client.post("/api/cloak/up", json={"accept_legal": True, "wait_tor": 0})
    assert r.status_code == 409
    release_owner()


def test_cloak_up_rejects_empty_enabled(client, isolated):
    cfg = load_config()
    cfg.accepted_legal_notice = True
    cfg.chains = [
        ChainConfig(
            name="hollow",
            profile=ProfileName.CUSTOM,
            hops=[
                HopConfig(
                    id="off",
                    type=HopType.TOR,
                    host="127.0.0.1",
                    port=9050,
                    enabled=False,
                )
            ],
            policy=ChainPolicy(min_hops=1, fail_closed=True),
        )
    ]
    cfg.active_chain = "hollow"
    save_config(cfg)
    r = client.post("/api/cloak/up", json={"accept_legal": True, "wait_tor": 0})
    assert r.status_code == 400


def test_status_probe_does_not_claim_running_from_port(client, monkeypatch):
    monkeypatch.setattr("trenchcoat.engine.tor_detect.port_open", lambda *a, **k: True)
    r = client.get("/api/status")
    assert r.status_code == 200
    data = r.json()
    assert data["running"] is False
    assert data["source"] == "probe"
    assert data.get("owner_alive") is False
    blob = " ".join(data.get("messages") or []).lower()
    assert "cloaked" in blob or "no cloak" in blob


def test_stale_bus_does_not_claim_running(client, isolated):
    from trenchcoat.engine.status_bus import write_status

    write_status({"running": True, "chain_name": "fake", "messages": ["should not cloaked"]})
    r = client.get("/api/status")
    data = r.json()
    assert data["running"] is False
    assert data.get("stale") is True or data["source"] == "probe"


def test_cloak_up_reports_failure_if_child_exits(client, monkeypatch):
    client.put(
        "/api/chain",
        json={
            "name": "custom-desk",
            "hops": [
                {"id": "tor-local", "type": "tor", "host": "127.0.0.1", "port": 9050, "enabled": True}
            ],
        },
    )
    real_popen = subprocess.Popen

    def fake_popen(*_a, **_k):
        return real_popen(
            [sys.executable, "-c", "raise SystemExit(1)"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    monkeypatch.setattr("trenchcoat.api.server.subprocess.Popen", fake_popen)
    r = client.post("/api/cloak/up", json={"accept_legal": True, "wait_tor": 0})
    assert r.status_code == 503, r.text
    alive, _ = owner_alive()
    assert alive is False


def test_cloak_up_pending_if_child_lives(client, monkeypatch):
    client.put(
        "/api/chain",
        json={
            "name": "custom-desk",
            "hops": [
                {"id": "tor-local", "type": "tor", "host": "127.0.0.1", "port": 9050, "enabled": True}
            ],
        },
    )
    held: list[subprocess.Popen] = []
    real_popen = subprocess.Popen

    def fake_popen(*_a, **_k):
        flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        proc = real_popen(
            [sys.executable, "-c", "import time; time.sleep(60)"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=flags,
        )
        held.append(proc)
        return proc

    monkeypatch.setattr("trenchcoat.api.server.subprocess.Popen", fake_popen)
    try:
        r = client.post("/api/cloak/up", json={"accept_legal": True, "wait_tor": 0})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["ok"] is True
        assert body.get("running") is False
        assert body.get("pending") is True
        assert "not cloaked" in body["message"].lower()
        down = client.post("/api/cloak/down")
        assert down.status_code == 200
    finally:
        for proc in held:
            if proc.poll() is None:
                proc.kill()
                proc.wait(timeout=3)
        release_owner()


def test_cloak_down_stale_fingerprint_does_not_kill(client, isolated):
    proc = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(60)"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        claim_owner(proc.pid)
        rec_path = isolated / "cloak.pid"
        rec = json.loads(rec_path.read_text(encoding="utf-8"))
        rec["create_time"] = float(rec["create_time"]) - 99999
        rec_path.write_text(json.dumps(rec), encoding="utf-8")
        r = client.post("/api/cloak/down")
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["ok"] is True
        assert body["mode"] == "stale"
        assert "not killed" in body["message"].lower()
        assert proc.poll() is None
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=3)
        release_owner()


def test_pid_lock_down_stops_process(client, isolated):
    proc = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(60)"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        claim_owner(proc.pid)
        alive, pid = owner_alive()
        assert alive is True
        assert pid == proc.pid
        r = client.post("/api/cloak/down")
        assert r.status_code == 200, r.text
        assert r.json()["ok"] is True
        deadline = time.time() + 8
        while proc.poll() is None and time.time() < deadline:
            time.sleep(0.1)
        assert proc.poll() is not None
        alive2, _ = owner_alive()
        assert alive2 is False
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=3)
        release_owner()
