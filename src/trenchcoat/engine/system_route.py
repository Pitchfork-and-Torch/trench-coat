"""
System-wide routing helpers (Phase 2 Circuit City).

Full transparent redirect (WFP/nftables/pf) requires elevated privileges.
This module provides:
  - Soft system proxy (Windows WinINET / user-level)
  - Script emitters for nftables / pf hard routing
  - Apply/revert APIs that never leave the system bricked without undo
"""

from __future__ import annotations

import logging
import platform
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger("trenchcoat.sysroute")


@dataclass
class RouteActionResult:
    ok: bool
    platform: str = field(default_factory=platform.system)
    mode: str = "none"
    messages: list[str] = field(default_factory=list)
    undo_hint: str = ""


class SystemRouter:
    """Best-effort OS routing / system proxy control."""

    def __init__(self, socks_host: str = "127.0.0.1", socks_port: int = 1080) -> None:
        self.socks_host = socks_host
        self.socks_port = socks_port
        self._applied: list[str] = []

    def apply_soft(self) -> RouteActionResult:
        system = platform.system()
        if system == "Windows":
            return self._win_soft_proxy(enable=True)
        if system == "Darwin":
            return RouteActionResult(
                ok=False,
                mode="soft",
                messages=[
                    "macOS soft system proxy: set SOCKS via System Settings → Network → Details → Proxies, "
                    f"or: networksetup -setsocksfirewallproxy Wi-Fi {self.socks_host} {self.socks_port}"
                ],
                undo_hint="networksetup -setsocksfirewallproxystate Wi-Fi off",
            )
        return RouteActionResult(
            ok=False,
            mode="soft",
            messages=[
                "Linux: use packaging/nft-trenchcoat.nft or set app-level SOCKS. "
                "GNOME: gsettings set org.gnome.system.proxy mode 'manual'"
            ],
            undo_hint="gsettings set org.gnome.system.proxy mode 'none'",
        )

    def revert_soft(self) -> RouteActionResult:
        if platform.system() == "Windows":
            return self._win_soft_proxy(enable=False)
        return RouteActionResult(ok=True, mode="soft", messages=["No soft proxy state to clear on this OS."])

    def emit_hard_scripts(self, out_dir: Path) -> list[Path]:
        out_dir.mkdir(parents=True, exist_ok=True)
        written: list[Path] = []
        nft = out_dir / "nft-trenchcoat.nft"
        nft.write_text(
            f"""# Trench Coat nftables sketch — REQUIRES root review before load
# Allow loopback + established + local SOCKS {self.socks_port}; block other egress when armed.
table inet trenchcoat {{
  chain output {{
    type filter hook output priority 0; policy accept;
    oif "lo" accept
    ct state established,related accept
    meta l4proto {{ tcp, udp }} ip daddr 127.0.0.1 tcp dport {self.socks_port} accept
    # Uncomment only after verifying unlock path:
    # meta l4proto {{ tcp, udp }} reject
  }}
}}
""",
            encoding="utf-8",
        )
        written.append(nft)
        pf = out_dir / "pf-trenchcoat.conf"
        pf.write_text(
            f"""# macOS pf anchor sketch — root + undo path required
# pass quick on lo0 all
# pass out quick proto tcp to 127.0.0.1 port {self.socks_port}
# block out quick all
""",
            encoding="utf-8",
        )
        written.append(pf)
        win = out_dir / "windows-wfp-notes.md"
        win.write_text(
            """# Windows WFP / full-tunnel notes

Full transparent redirect needs a signed WFP callout or a userspace divert driver.
MVP soft path: WinINET SOCKS via `trench route soft`.

Hard path (future):
- WFP ALE_AUTH_CONNECT filter allowing only Tor + Trench entry
- Always ship disable script before enable
- Never install permanent blocks without operator confirmation
""",
            encoding="utf-8",
        )
        written.append(win)
        return written

    def _win_soft_proxy(self, enable: bool) -> RouteActionResult:
        # WinHTTP is for services; for user browsers WinINET registry is more common.
        # Use netsh winhttp as a documented soft path (services / some tools).
        msgs: list[str] = []
        try:
            if enable:
                proxy = f"socks={self.socks_host}:{self.socks_port}"
                r = subprocess.run(
                    ["netsh", "winhttp", "set", "proxy", proxy],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if r.returncode != 0:
                    return RouteActionResult(
                        ok=False,
                        mode="soft-winhttp",
                        messages=[r.stderr or r.stdout or "netsh failed"],
                    )
                self._applied.append("winhttp")
                msgs.append(f"WinHTTP proxy set to {proxy}")
                msgs.append(
                    "Browsers often use WinINET — also set SOCKS in browser or use app-level proxy."
                )
                return RouteActionResult(
                    ok=True,
                    mode="soft-winhttp",
                    messages=msgs,
                    undo_hint="trench route revert  OR  netsh winhttp reset proxy",
                )
            r = subprocess.run(
                ["netsh", "winhttp", "reset", "proxy"],
                capture_output=True,
                text=True,
                check=False,
            )
            msgs.append(r.stdout.strip() or "WinHTTP proxy reset")
            return RouteActionResult(ok=r.returncode == 0, mode="soft-winhttp", messages=msgs)
        except Exception as exc:  # noqa: BLE001
            return RouteActionResult(ok=False, mode="soft-winhttp", messages=[str(exc)])
