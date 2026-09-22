"""Cross-process status bus - file-backed so `trench gui` can see `trench up`."""

from __future__ import annotations

import json
import os
import signal
import time
from pathlib import Path
from typing import Any

from trenchcoat.config.loader import data_dir

# create_time float compare; PID reuse on Windows is the real threat.
_CREATE_TIME_SLOP = 1.0


class OwnerBusy(RuntimeError):
    """Another process already owns the cloak data plane."""

    def __init__(self, pid: int) -> None:
        super().__init__(f"cloak already owned by pid {pid}")
        self.pid = pid


def status_path() -> Path:
    return data_dir() / "runtime_status.json"


def pid_path() -> Path:
    return data_dir() / "cloak.pid"


def stop_request_path() -> Path:
    return data_dir() / "cloak.stop"


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


def request_stop() -> None:
    path = stop_request_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(time.time()), encoding="utf-8")


def stop_requested() -> bool:
    return stop_request_path().exists()


def clear_stop_request() -> None:
    path = stop_request_path()
    if path.exists():
        try:
            path.unlink()
        except OSError:
            pass


def _pid_running(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        import psutil

        proc = psutil.Process(pid)
        return bool(proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE)
    except Exception:  # noqa: BLE001
        return False


def process_create_time(pid: int) -> float | None:
    if pid <= 0:
        return None
    try:
        import psutil

        return float(psutil.Process(pid).create_time())
    except Exception:  # noqa: BLE001
        return None


_CLOAK_NAMES = {"trench", "trench.exe", "trenchcoat", "trenchcoat.exe"}


def looks_like_cloak(pid: int) -> bool:
    """Best-effort argv check. Do not match the repo folder name as a substring."""
    if pid <= 0:
        return False
    try:
        import psutil

        proc = psutil.Process(pid)
        name = (proc.name() or "").lower()
        if name in _CLOAK_NAMES:
            return True
        parts = [str(x) for x in (proc.cmdline() or [])]
        lower = [p.lower() for p in parts]
        for i, p in enumerate(lower):
            if p in {"-m", "--module"} and i + 1 < len(lower):
                mod = lower[i + 1]
                if mod == "trenchcoat" or mod.startswith("trenchcoat."):
                    return True
            base = Path(p.replace("\\", "/")).name
            if base in _CLOAK_NAMES:
                return True
        return False
    except Exception:  # noqa: BLE001
        return False


def _parse_owner_record(raw: str) -> dict[str, Any] | None:
    text = raw.strip()
    if not text:
        return None
    if text[0] == "{":
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return None
        try:
            pid = int(data.get("pid") or 0)
        except (TypeError, ValueError):
            return None
        if pid <= 0:
            return None
        rec: dict[str, Any] = {"pid": pid, "kind": str(data.get("kind") or "cloak")}
        ct = data.get("create_time")
        if ct is not None:
            try:
                rec["create_time"] = float(ct)
            except (TypeError, ValueError):
                pass
        claimed = data.get("claimed_at")
        if claimed is not None:
            try:
                rec["claimed_at"] = float(claimed)
            except (TypeError, ValueError):
                pass
        rec["breakaway"] = bool(data.get("breakaway"))
        return rec
    try:
        pid = int(text)
    except ValueError:
        return None
    if pid <= 0:
        return None
    return {"pid": pid, "kind": "cloak"}


def read_owner_record() -> dict[str, Any] | None:
    path = pid_path()
    if not path.exists():
        return None
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return None
    return _parse_owner_record(raw)


def read_owner_pid() -> int | None:
    rec = read_owner_record()
    if rec is None:
        return None
    pid = int(rec["pid"])
    return pid if pid > 0 else None


def fingerprint_matches(record: dict[str, Any] | None) -> bool:
    """True only if the live process is the same one we claimed."""
    if not record:
        return False
    pid = int(record.get("pid") or 0)
    if not _pid_running(pid):
        return False
    expected = record.get("create_time")
    if expected is None:
        # Legacy bare pid file: refuse to treat as live owner unless cmdline is trench.
        return looks_like_cloak(pid)
    live = process_create_time(pid)
    if live is None:
        return False
    return abs(live - float(expected)) <= _CREATE_TIME_SLOP


def owner_alive() -> tuple[bool, int | None]:
    rec = read_owner_record()
    if rec is None:
        return False, None
    pid = int(rec["pid"])
    if fingerprint_matches(rec):
        return True, pid
    return False, pid


def owner_blocks(pid: int) -> int | None:
    """Return the blocking owner pid if another live cloak owns the plane."""
    alive, existing = owner_alive()
    if alive and existing is not None and int(existing) != int(pid):
        return int(existing)
    return None


def claim_owner(pid: int, *, breakaway: bool = False) -> None:
    pid = int(pid)
    blocker = owner_blocks(pid)
    if blocker is not None:
        raise OwnerBusy(blocker)
    rec = {
        "pid": pid,
        "create_time": process_create_time(pid),
        "claimed_at": time.time(),
        "kind": "cloak",
        "breakaway": bool(breakaway),
    }
    path = pid_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(rec), encoding="utf-8")
    tmp.replace(path)
    clear_stop_request()


def release_owner() -> None:
    path = pid_path()
    if path.exists():
        try:
            path.unlink()
        except OSError:
            pass
    clear_stop_request()
    clear_status()


def _graceful_signal(pid: int, *, breakaway: bool = False) -> None:
    """Ask the cloak process to exit. Never CTRL_BREAK the shared console."""
    try:
        import psutil

        proc = psutil.Process(pid)
    except Exception:  # noqa: BLE001
        return
    if os.name == "nt":
        if breakaway:
            try:
                os.kill(pid, signal.CTRL_BREAK_EVENT)  # type: ignore[attr-defined]
                return
            except Exception:  # noqa: BLE001
                pass
        try:
            proc.terminate()
        except Exception:  # noqa: BLE001
            pass
        return
    try:
        proc.send_signal(signal.SIGTERM)
    except Exception:  # noqa: BLE001
        try:
            proc.terminate()
        except Exception:  # noqa: BLE001
            pass


def _wait_dead(pid: int, timeout: float) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if not _pid_running(pid):
            return True
        time.sleep(0.1)
    return not _pid_running(pid)


def stop_owner(*, timeout: float = 4.0) -> dict[str, Any]:
    """Stop the pid-owned cloak. Never kill a reused PID.

    Order: stop file (so `trench up` can engine.stop), then graceful signal,
    then kill only if the fingerprint still matches.
    """
    rec = read_owner_record()
    if rec is None:
        release_owner()
        return {"ok": True, "mode": "idle", "pid": None}

    pid = int(rec["pid"])
    if not fingerprint_matches(rec):
        release_owner()
        return {
            "ok": True,
            "mode": "stale",
            "pid": pid,
            "error": "owner pid does not match cloak fingerprint; lock cleared, process not killed",
        }

    request_stop()
    if _wait_dead(pid, min(timeout, 2.0)):
        release_owner()
        return {"ok": True, "mode": "subprocess", "pid": pid, "graceful": True}

    if not fingerprint_matches(rec):
        release_owner()
        return {
            "ok": True,
            "mode": "stale",
            "pid": pid,
            "error": "owner pid changed during stop; lock cleared, process not killed",
        }

    try:
        import psutil

        proc = psutil.Process(pid)
        _graceful_signal(pid, breakaway=bool(rec.get("breakaway")))
        try:
            proc.wait(timeout=max(1.0, timeout - 1.0))
        except psutil.TimeoutExpired:
            if fingerprint_matches(rec):
                proc.kill()
                proc.wait(timeout=3)
    except Exception as exc:  # noqa: BLE001
        release_owner()
        return {"ok": False, "mode": "subprocess", "pid": pid, "error": str(exc)}

    release_owner()
    return {"ok": True, "mode": "subprocess", "pid": pid, "graceful": False}
