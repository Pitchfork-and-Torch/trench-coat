"""Cross-process status bus - file-backed so `trench gui` can see `trench up`."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from trenchcoat.config.loader import data_dir


class OwnerBusy(RuntimeError):
    """Another process already owns the cloak data plane."""

    def __init__(self, pid: int) -> None:
        super().__init__(f"cloak already owned by pid {pid}")
        self.pid = pid


def status_path() -> Path:
    return data_dir() / "runtime_status.json"


def pid_path() -> Path:
    return data_dir() / "cloak.pid"


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


def _pid_running(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        import psutil

        proc = psutil.Process(pid)
        return bool(proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE)
    except Exception:  # noqa: BLE001
        return False


def read_owner_pid() -> int | None:
    path = pid_path()
    if not path.exists():
        return None
    try:
        raw = path.read_text(encoding="utf-8").strip()
        pid = int(raw)
    except (OSError, ValueError):
        return None
    return pid if pid > 0 else None


def owner_alive() -> tuple[bool, int | None]:
    pid = read_owner_pid()
    if pid is None:
        return False, None
    if _pid_running(pid):
        return True, pid
    return False, pid


def claim_owner(pid: int) -> None:
    alive, existing = owner_alive()
    if alive and existing is not None and existing != pid:
        raise OwnerBusy(existing)
    path = pid_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(int(pid)), encoding="utf-8")


def release_owner() -> None:
    path = pid_path()
    if path.exists():
        try:
            path.unlink()
        except OSError:
            pass
    clear_status()


def _looks_like_cloak_process(proc: Any) -> bool:
    """True if cmdline/name looks like a trench cloak owner (guards PID reuse)."""
    try:
        name = (proc.name() or "").lower()
        cmd = " ".join(proc.cmdline() or []).lower()
    except Exception:  # noqa: BLE001
        return False
    blob = f"{name} {cmd}"
    markers = (
        "trenchcoat",
        "trench-coat",
        "trenchcoat.cli",
        "trenchcoat.__main__",
        "/trench ",
        "\trench ",
        "trench.exe",
        "trench ",
    )
    if any(m in blob for m in markers):
        return True
    # `trench` as argv0 / script basename
    try:
        argv0 = (proc.cmdline() or [""])[0]
    except Exception:  # noqa: BLE001
        argv0 = ""
    base = Path(argv0).name.lower() if argv0 else ""
    return base in {"trench", "trench.exe", "trenchcoat", "trenchcoat.exe"}


def stop_owner(*, timeout: float = 8.0) -> dict[str, Any]:
    """Terminate the pid-owned cloak process. Safe if already idle.

    Refuses to signal a PID that no longer looks like a trench process so a
    recycled OS PID cannot be killed by Disengage.
    """
    alive, pid = owner_alive()
    if not alive or pid is None:
        release_owner()
        return {"ok": True, "mode": "idle", "pid": pid}

    try:
        import psutil

        proc = psutil.Process(pid)
        if not _looks_like_cloak_process(proc):
            # PID reused by an unrelated process — clear the lock, do not signal it.
            release_owner()
            return {
                "ok": True,
                "mode": "stale-pid",
                "pid": pid,
                "message": "cleared stale owner; pid no longer pointed at a trench process",
            }
        proc.terminate()
        try:
            proc.wait(timeout=timeout)
        except psutil.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=3)
    except Exception as exc:  # noqa: BLE001
        release_owner()
        return {"ok": False, "mode": "subprocess", "pid": pid, "error": str(exc)}

    release_owner()
    return {"ok": True, "mode": "subprocess", "pid": pid}
