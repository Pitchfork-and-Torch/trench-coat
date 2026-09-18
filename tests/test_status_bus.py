"""PID-owner file: Disengage must not kill a recycled non-trench PID."""

from __future__ import annotations

import os
from trenchcoat.engine import status_bus


class _FakeProc:
    def __init__(self, pid: int, name: str, cmdline: list[str]) -> None:
        self.pid = pid
        self._name = name
        self._cmdline = cmdline
        self.terminated = False
        self.killed = False

    def name(self) -> str:
        return self._name

    def cmdline(self) -> list[str]:
        return list(self._cmdline)

    def terminate(self) -> None:
        self.terminated = True

    def kill(self) -> None:
        self.killed = True

    def wait(self, timeout: float | None = None) -> int:
        _ = timeout
        return 0


def test_looks_like_cloak_process_positive() -> None:
    proc = _FakeProc(1, "python", ["python", "-m", "trenchcoat", "up"])
    assert status_bus._looks_like_cloak_process(proc) is True
    proc2 = _FakeProc(1, "trench", ["/usr/bin/trench", "up"])
    assert status_bus._looks_like_cloak_process(proc2) is True


def test_looks_like_cloak_process_rejects_unrelated() -> None:
    proc = _FakeProc(1, "firefox", ["/usr/lib/firefox/firefox"])
    assert status_bus._looks_like_cloak_process(proc) is False


def test_stop_owner_refuses_recycled_pid(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(status_bus, "data_dir", lambda: tmp_path)
    # Claim with our pid, then pretend that pid is a recycled firefox.
    status_bus.claim_owner(os.getpid())
    fake = _FakeProc(os.getpid(), "firefox", ["/usr/lib/firefox/firefox"])

    class _PS:
        @staticmethod
        def Process(pid: int) -> _FakeProc:
            assert pid == os.getpid()
            return fake

        class TimeoutExpired(Exception):
            pass

    monkeypatch.setattr(status_bus, "owner_alive", lambda: (True, os.getpid()))
    import sys

    monkeypatch.setitem(sys.modules, "psutil", _PS)

    result = status_bus.stop_owner()
    assert result["ok"] is True
    assert result["mode"] == "stale-pid"
    assert fake.terminated is False
    assert fake.killed is False
    # Stale owner file cleared so a fresh engage can proceed
    assert status_bus.read_owner_pid() is None


def test_stop_owner_terminates_trench_process(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(status_bus, "data_dir", lambda: tmp_path)
    status_bus.claim_owner(os.getpid())
    fake = _FakeProc(os.getpid(), "python", ["python", "-m", "trenchcoat.cli", "up"])

    class _PS:
        @staticmethod
        def Process(pid: int) -> _FakeProc:
            return fake

        class TimeoutExpired(Exception):
            pass

    monkeypatch.setattr(status_bus, "owner_alive", lambda: (True, os.getpid()))
    import sys

    monkeypatch.setitem(sys.modules, "psutil", _PS)

    result = status_bus.stop_owner()
    assert result["ok"] is True
    assert result["mode"] == "subprocess"
    assert fake.terminated is True
    assert status_bus.read_owner_pid() is None
