"""External process managers for WG / SS / Hysteria2 / PT bridges."""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
import signal
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

log = logging.getLogger("trenchcoat.proc")


@dataclass
class ManagedProcess:
    name: str
    pid: int | None = None
    cmd: list[str] = field(default_factory=list)
    log_path: str | None = None


class ProcessManager:
    """Track and stop child processes started for hop daemons."""

    def __init__(self) -> None:
        self._children: dict[str, subprocess.Popen[str]] = {}

    def which(self, *names: str) -> str | None:
        for n in names:
            path = shutil.which(n)
            if path:
                return path
        return None

    def is_running(self, name: str) -> bool:
        proc = self._children.get(name)
        return proc is not None and proc.poll() is None

    def start(
        self,
        name: str,
        cmd: Sequence[str],
        cwd: str | None = None,
        env: dict[str, str] | None = None,
    ) -> ManagedProcess:
        if self.is_running(name):
            p = self._children[name]
            return ManagedProcess(name=name, pid=p.pid, cmd=list(cmd))
        full_env = os.environ.copy()
        if env:
            full_env.update(env)
        log.info("starting hop process %s: %s", name, " ".join(cmd))
        proc = subprocess.Popen(
            list(cmd),
            cwd=cwd,
            env=full_env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        self._children[name] = proc
        return ManagedProcess(name=name, pid=proc.pid, cmd=list(cmd))

    def stop(self, name: str) -> bool:
        proc = self._children.pop(name, None)
        if not proc:
            return False
        if proc.poll() is None:
            try:
                if os.name == "nt":
                    proc.terminate()
                else:
                    proc.send_signal(signal.SIGTERM)
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
            except Exception as exc:  # noqa: BLE001
                log.warning("stop %s: %s", name, exc)
                return False
        return True

    def stop_all(self) -> None:
        for name in list(self._children):
            self.stop(name)


# Module singleton for CLI lifetime
MANAGER = ProcessManager()


async def wait_port(host: str, port: int, timeout: float = 30.0) -> bool:
    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < deadline:
        try:
            reader, writer = await asyncio.open_connection(host, port)
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:  # noqa: BLE001
                pass
            return True
        except Exception:  # noqa: BLE001
            await asyncio.sleep(0.4)
    return False


def resolve_binary(options: dict, *keys_and_defaults: str) -> str | None:
    for key in keys_and_defaults:
        if key in options and options[key]:
            p = Path(str(options[key]))
            if p.exists():
                return str(p)
        found = MANAGER.which(key)
        if found:
            return found
    return None
