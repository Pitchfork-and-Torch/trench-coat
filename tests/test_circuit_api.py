"""Circuit Desk control API: templates, chain PUT, pid-owned Engage/Disengage."""

from __future__ import annotations

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
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("TRENCH_COAT_CONFIG", str(tmp_path / "config.yaml"))
    monkeypatch.setattr("trenchcoat.config.loader.data_dir", lambda: tmp_path)
    monkeypatch.setattr("trenchcoat.engine.status_bus.data_dir", lambda: tmp_path)
    release_owner()
    yield tmp_path
    release_owner()


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
