"""Pid lock: self-claim, fingerprint, refuse PID reuse kills."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time

from trenchcoat.engine.status_bus import (
    OwnerBusy,
    claim_owner,
    looks_like_cloak,
    owner_alive,
    owner_blocks,
    read_owner_record,
    release_owner,
    request_stop,
    stop_owner,
    stop_requested,
)


def test_looks_like_cloak_ignores_repo_path(isolated):
    # pytest argv includes .../trench-coat/... ; that must not count as the cloak.
    assert looks_like_cloak(os.getpid()) is False


def test_self_pid_is_not_a_blocker(isolated):
    me = os.getpid()
    claim_owner(me)
    claim_owner(me)
    alive, pid = owner_alive()
    assert alive is True
    assert pid == me
    assert owner_blocks(me) is None
    rec = read_owner_record()
    assert rec is not None
    assert rec["pid"] == me
    assert rec.get("create_time") is not None
    release_owner()
    alive2, _ = owner_alive()
    assert alive2 is False


def test_other_pid_blocks(isolated):
    proc = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(60)"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        claim_owner(proc.pid)
        assert owner_blocks(os.getpid()) == proc.pid
        try:
            claim_owner(os.getpid())
            raise AssertionError("expected OwnerBusy")
        except OwnerBusy as exc:
            assert exc.pid == proc.pid
    finally:
        proc.kill()
        proc.wait(timeout=3)
        release_owner()


def test_stop_owner_refuses_pid_reuse(isolated):
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
        result = stop_owner()
        assert result["mode"] == "stale"
        assert proc.poll() is None
        alive, _ = owner_alive()
        assert alive is False
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=3)
        release_owner()


def test_legacy_bare_pid_does_not_kill_unrelated(isolated):
    (isolated / "cloak.pid").write_text(str(os.getpid()), encoding="utf-8")
    result = stop_owner()
    assert result["mode"] == "stale"
    assert result.get("pid") == os.getpid()


def test_stop_file_is_honored(isolated):
    request_stop()
    assert stop_requested() is True
    release_owner()
    assert stop_requested() is False


def test_stop_owner_kills_matching_child(isolated):
    proc = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(60)"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        claim_owner(proc.pid)
        result = stop_owner(timeout=2.0)
        assert result["ok"] is True
        assert result["mode"] == "subprocess"
        deadline = time.time() + 8
        while proc.poll() is None and time.time() < deadline:
            time.sleep(0.05)
        assert proc.poll() is not None
        alive, _ = owner_alive()
        assert alive is False
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=3)
        release_owner()
