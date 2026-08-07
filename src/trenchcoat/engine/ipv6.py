"""IPv6 hardening helpers (disable guidance + best-effort automation)."""

from __future__ import annotations

import logging
import platform
import subprocess
from dataclasses import dataclass, field

log = logging.getLogger("trenchcoat.ipv6")


@dataclass
class IPv6Action:
    ok: bool
    messages: list[str] = field(default_factory=list)
    requires_admin: bool = False


def status_hint() -> IPv6Action:
    system = platform.system()
    msgs = []
    if system == "Windows":
        msgs.append("Inspect: Get-NetAdapterBinding -ComponentID ms_tcpip6")
        msgs.append(
            "Disable (admin): Disable-NetAdapterBinding -Name 'Wi-Fi' -ComponentID ms_tcpip6"
        )
    elif system == "Linux":
        msgs.append("sysctl net.ipv6.conf.all.disable_ipv6")
        msgs.append("Enable session: sudo sysctl -w net.ipv6.conf.all.disable_ipv6=1")
    elif system == "Darwin":
        msgs.append("networksetup -listallnetworkservices")
        msgs.append("networksetup -setv6off Wi-Fi")
    else:
        msgs.append(f"No IPv6 automation for {system}")
    return IPv6Action(ok=True, messages=msgs)


def try_disable(dry_run: bool = True) -> IPv6Action:
    """Best-effort disable. Default dry_run=True to avoid surprise lockouts."""
    system = platform.system()
    if dry_run:
        h = status_hint()
        h.messages.insert(0, "dry-run: no changes applied")
        return h
    if system == "Linux":
        try:
            r = subprocess.run(
                ["sysctl", "-w", "net.ipv6.conf.all.disable_ipv6=1"],
                capture_output=True,
                text=True,
                check=False,
            )
            return IPv6Action(
                ok=r.returncode == 0,
                messages=[r.stdout or r.stderr or "sysctl invoked"],
                requires_admin=True,
            )
        except Exception as exc:  # noqa: BLE001
            return IPv6Action(ok=False, messages=[str(exc)], requires_admin=True)
    return IPv6Action(
        ok=False,
        requires_admin=True,
        messages=[
            f"Automated IPv6 disable not forced on {system}. "
            "Use platform commands from `trench ipv6 status`."
        ],
    )
