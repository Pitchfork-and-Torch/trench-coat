"""
Kill-switch — fail closed when the cloak tears.

Platform strategies:
  - Windows: netsh advfirewall rules (admin), allow-list loopback proxy ports
  - Linux: nftables script emit (+ optional apply)
  - macOS: pf anchor script emit

Soft kill-switch always (local proxy refuses direct bypass).
Hard kill-switch is **opt-in**, operator-confirmed, and always writes an undo script first.
"""

from __future__ import annotations

import logging
import platform
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger("trenchcoat.killswitch")

RULE_PREFIX = "TrenchCoat"


@dataclass
class KillSwitchState:
    active: bool = False
    strict: bool = True
    platform: str = field(default_factory=platform.system)
    messages: list[str] = field(default_factory=list)
    hard_enabled: bool = False
    undo_script: str | None = None


class KillSwitch:
    def __init__(self, strict: bool = True) -> None:
        self.state = KillSwitchState(strict=strict)

    def arm(self, allow_uid_ports: list[int] | None = None) -> KillSwitchState:
        """Activate kill-switch. Soft always; hard only via arm_hard()."""
        self.state.active = True
        self.state.messages.clear()
        self.state.messages.append(
            "Soft kill-switch armed: app traffic should use the cloak entry only."
        )
        ports = allow_uid_ports or []
        if ports:
            self.state.messages.append(
                f"Hard mode (opt-in) would allow loopback ports: {ports}. "
                "Run `trench killswitch hard --confirm` as admin/root when ready."
            )
        return self.state

    def arm_hard(
        self,
        allow_ports: list[int],
        *,
        confirm: bool = False,
        dry_run: bool = False,
        undo_dir: Path | None = None,
    ) -> KillSwitchState:
        """
        Opt-in hard kill-switch (Phase 6 Iron Collar).

        Safety rules:
          1. Writes an undo/disable script *before* applying any block.
          2. Requires confirm=True (CLI maps --confirm).
          3. dry_run=True only writes scripts and describes actions.
        """
        self.state.messages.clear()
        self.state.active = True
        if not allow_ports:
            allow_ports = [1080]

        undo_dir = undo_dir or Path.home() / ".trenchcoat" / "killswitch"
        undo_dir.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%d-%H%M%S")
        undo_path = undo_dir / f"disable-hard-{stamp}"
        system = platform.system()

        if system == "Windows":
            undo_file = undo_path.with_suffix(".ps1")
            self._write_windows_undo(undo_file)
            plan = self._windows_hard_plan(allow_ports)
        elif system == "Linux":
            undo_file = undo_path.with_suffix(".sh")
            self._write_linux_undo(undo_file)
            plan = self._linux_hard_plan(allow_ports)
        elif system == "Darwin":
            undo_file = undo_path.with_suffix(".sh")
            self._write_darwin_undo(undo_file)
            plan = self._darwin_hard_plan(allow_ports)
        else:
            self.state.messages.append(f"Hard kill-switch not implemented for {system}.")
            return self.state

        self.state.undo_script = str(undo_file)
        self.state.messages.append(f"Undo script written first: {undo_file}")
        for line in plan["describe"]:
            self.state.messages.append(line)

        if dry_run:
            self.state.messages.append("Dry-run: no firewall rules applied.")
            self.state.hard_enabled = False
            return self.state

        if not confirm:
            self.state.messages.append(
                "Hard mode NOT applied. Re-run with --confirm after reviewing the undo script "
                "(and ideally after testing soft cloak connectivity)."
            )
            self.state.hard_enabled = False
            return self.state

        try:
            applied = plan["apply"]()
            self.state.hard_enabled = applied
            if applied:
                self.state.messages.append(
                    "Hard kill-switch ACTIVE. Keep the undo script handy before rebooting or traveling."
                )
            else:
                self.state.messages.append(
                    "Hard kill-switch could not be fully applied (privileges?). Soft mode remains."
                )
        except Exception as exc:  # noqa: BLE001
            self.state.hard_enabled = False
            self.state.messages.append(f"Hard kill-switch failed: {exc}")
            log.warning("hard kill-switch failed: %s", exc)
        return self.state

    def disarm(self) -> KillSwitchState:
        self.state.active = False
        system = platform.system()
        try:
            if system == "Windows":
                self._disarm_windows()
            elif system == "Linux":
                self._disarm_linux()
            elif system == "Darwin":
                self._disarm_darwin()
        except Exception as exc:  # noqa: BLE001
            self.state.messages.append(f"Disarm issue: {exc}")
        self.state.hard_enabled = False
        self.state.messages.append("Kill-switch disarmed (best-effort rule cleanup).")
        return self.state

    def emit_hard_bundle(
        self, out_dir: Path, allow_ports: list[int] | None = None
    ) -> list[Path]:
        """Write reviewable hard-mode scripts without applying them."""
        out_dir.mkdir(parents=True, exist_ok=True)
        ports = allow_ports or [1080]
        written: list[Path] = []
        system = platform.system()
        if system == "Windows" or True:
            # Always emit all platform bundles for operators cross-building docs
            p = out_dir / "windows-hard-killswitch.ps1"
            p.write_text(self._windows_apply_script(ports), encoding="utf-8")
            written.append(p)
            u = out_dir / "windows-hard-killswitch-undo.ps1"
            self._write_windows_undo(u)
            written.append(u)
        p = out_dir / "linux-hard-killswitch.nft"
        p.write_text(self._linux_nft_table(ports), encoding="utf-8")
        written.append(p)
        u = out_dir / "linux-hard-killswitch-undo.sh"
        self._write_linux_undo(u)
        written.append(u)
        p = out_dir / "macos-hard-killswitch.pf"
        p.write_text(self._darwin_pf_rules(ports), encoding="utf-8")
        written.append(p)
        u = out_dir / "macos-hard-killswitch-undo.sh"
        self._write_darwin_undo(u)
        written.append(u)
        return written

    def _run(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=False,
            shell=False,
        )

    # --- Windows ---

    def _windows_hard_plan(self, allow_ports: list[int]) -> dict:
        def apply() -> bool:
            # Allow loopback to cloak entry first
            for port in allow_ports:
                name = f"{RULE_PREFIX}-Allow-Local-{port}"
                r = self._run(
                    [
                        "netsh",
                        "advfirewall",
                        "firewall",
                        "add",
                        "rule",
                        f"name={name}",
                        "dir=out",
                        "action=allow",
                        "protocol=TCP",
                        "remoteip=127.0.0.1",
                        f"remoteport={port}",
                        "enable=yes",
                        "profile=any",
                    ]
                )
                if r.returncode != 0:
                    self.state.messages.append(
                        "Administrator privileges required for Windows hard kill-switch."
                    )
                    return False
            # Allow established-style DNS to localhost if needed is covered by allow rules
            block = f"{RULE_PREFIX}-Block-Outbound"
            # Delete existing block first (idempotent)
            self._run(
                ["netsh", "advfirewall", "firewall", "delete", "rule", f"name={block}"]
            )
            r = self._run(
                [
                    "netsh",
                    "advfirewall",
                    "firewall",
                    "add",
                    "rule",
                    f"name={block}",
                    "dir=out",
                    "action=block",
                    "enable=yes",
                    "profile=any",
                ]
            )
            if r.returncode != 0:
                self.state.messages.append(r.stderr or r.stdout or "block rule failed")
                return False
            # Critical: allow loopback general (some stacks need broader lo)
            lo = f"{RULE_PREFIX}-Allow-Loopback"
            self._run(
                ["netsh", "advfirewall", "firewall", "delete", "rule", f"name={lo}"]
            )
            self._run(
                [
                    "netsh",
                    "advfirewall",
                    "firewall",
                    "add",
                    "rule",
                    f"name={lo}",
                    "dir=out",
                    "action=allow",
                    "remoteip=127.0.0.1",
                    "enable=yes",
                    "profile=any",
                ]
            )
            return True

        return {
            "describe": [
                f"Windows hard plan: allow 127.0.0.1 TCP ports {allow_ports}, allow loopback, "
                f"then block other outbound via rule '{RULE_PREFIX}-Block-Outbound'.",
                "This can lock you out of the internet if the cloak is down — undo script is mandatory.",
            ],
            "apply": apply,
        }

    def _windows_apply_script(self, allow_ports: list[int]) -> str:
        allows = "\n".join(
            f'netsh advfirewall firewall add rule name="{RULE_PREFIX}-Allow-Local-{p}" '
            f"dir=out action=allow protocol=TCP remoteip=127.0.0.1 remoteport={p} enable=yes profile=any"
            for p in allow_ports
        )
        return f"""# Trench Coat hard kill-switch (Windows) — REVIEW before running as Administrator
# Undo: windows-hard-killswitch-undo.ps1 (always keep a copy offline)

$ErrorActionPreference = "Stop"
Write-Host "Trench Coat hard kill-switch — applying allow-list then outbound block"

{allows}
netsh advfirewall firewall delete rule name="{RULE_PREFIX}-Allow-Loopback" 2>$null
netsh advfirewall firewall add rule name="{RULE_PREFIX}-Allow-Loopback" dir=out action=allow remoteip=127.0.0.1 enable=yes profile=any
netsh advfirewall firewall delete rule name="{RULE_PREFIX}-Block-Outbound" 2>$null
netsh advfirewall firewall add rule name="{RULE_PREFIX}-Block-Outbound" dir=out action=block enable=yes profile=any

Write-Host "Hard kill-switch applied. Run the undo script if connectivity breaks."
"""

    def _write_windows_undo(self, path: Path) -> None:
        path.write_text(
            f"""# Trench Coat hard kill-switch UNDO (Windows) — run as Administrator
$ErrorActionPreference = "Continue"
$rules = netsh advfirewall firewall show rule name=all
foreach ($line in $rules) {{
  if ($line -match "Rule Name:\\s*(.+)$") {{
    $name = $Matches[1].Trim()
    if ($name -like "{RULE_PREFIX}-*") {{
      Write-Host "Deleting $name"
      netsh advfirewall firewall delete rule name="$name" | Out-Null
    }}
  }}
}}
Write-Host "Trench Coat firewall rules removed (best-effort)."
""",
            encoding="utf-8",
        )

    def _disarm_windows(self) -> None:
        result = self._run(
            ["netsh", "advfirewall", "firewall", "show", "rule", "name=all"]
        )
        if result.returncode != 0:
            return
        for line in result.stdout.splitlines():
            if "Rule Name:" in line and RULE_PREFIX in line:
                name = line.split(":", 1)[1].strip()
                self._run(
                    [
                        "netsh",
                        "advfirewall",
                        "firewall",
                        "delete",
                        "rule",
                        f"name={name}",
                    ]
                )

    # --- Linux ---

    def _linux_nft_table(self, allow_ports: list[int]) -> str:
        ports = ", ".join(str(p) for p in allow_ports)
        return f"""# Trench Coat hard kill-switch (nftables) — REVIEW as root before: nft -f thisfile
# Undo: linux-hard-killswitch-undo.sh

table inet trenchcoat_hard {{
  chain output {{
    type filter hook output priority 0; policy drop;
    oif "lo" accept
    ct state established,related accept
    ip daddr 127.0.0.1 tcp dport {{ {ports} }} accept
    ip6 daddr ::1 tcp dport {{ {ports} }} accept
  }}
}}
"""

    def _linux_hard_plan(self, allow_ports: list[int]) -> dict:
        def apply() -> bool:
            # Prefer writing nft file and loading if nft exists
            tmp = Path.home() / ".trenchcoat" / "killswitch" / "active-hard.nft"
            tmp.parent.mkdir(parents=True, exist_ok=True)
            tmp.write_text(self._linux_nft_table(allow_ports), encoding="utf-8")
            r = self._run(["nft", "-f", str(tmp)])
            if r.returncode != 0:
                self.state.messages.append(
                    "nft load failed (need root + nftables). Script left at "
                    f"{tmp}. Soft mode remains."
                )
                return False
            return True

        return {
            "describe": [
                f"Linux hard plan: nftables drop-by-default egress with lo + local ports {allow_ports}.",
            ],
            "apply": apply,
        }

    def _write_linux_undo(self, path: Path) -> None:
        path.write_text(
            """#!/bin/sh
# Trench Coat hard kill-switch UNDO (Linux)
nft delete table inet trenchcoat_hard 2>/dev/null || true
echo "Removed inet trenchcoat_hard (if present)."
""",
            encoding="utf-8",
        )
        try:
            path.chmod(path.stat().st_mode | 0o111)
        except OSError:
            pass

    def _disarm_linux(self) -> None:
        self._run(["nft", "delete", "table", "inet", "trenchcoat_hard"])

    # --- macOS ---

    def _darwin_pf_rules(self, allow_ports: list[int]) -> str:
        ports = ", ".join(str(p) for p in allow_ports)
        return f"""# Trench Coat hard kill-switch (pf) — REVIEW; load only with known unlock path
# Example (root): pfctl -a trenchcoat -f thisfile && pfctl -e
# Undo: macos-hard-killswitch-undo.sh

pass quick on lo0 all
pass out quick proto tcp from any to 127.0.0.1 port {{ {ports} }}
block out quick all
"""

    def _darwin_hard_plan(self, allow_ports: list[int]) -> dict:
        def apply() -> bool:
            tmp = Path.home() / ".trenchcoat" / "killswitch" / "active-hard.pf"
            tmp.parent.mkdir(parents=True, exist_ok=True)
            tmp.write_text(self._darwin_pf_rules(allow_ports), encoding="utf-8")
            # Loading pf without careful anchors can brick Macs — only load if pfctl works
            # and operator confirmed. Use anchor trenchcoat.
            r = self._run(["pfctl", "-a", "trenchcoat", "-f", str(tmp)])
            if r.returncode != 0:
                self.state.messages.append(
                    f"pfctl load failed (need root). Rules saved at {tmp}. Soft mode remains."
                )
                return False
            self._run(["pfctl", "-e"])
            return True

        return {
            "describe": [
                f"macOS hard plan: pf anchor allowing lo + 127.0.0.1 ports {allow_ports}, block other egress.",
            ],
            "apply": apply,
        }

    def _write_darwin_undo(self, path: Path) -> None:
        path.write_text(
            """#!/bin/sh
# Trench Coat hard kill-switch UNDO (macOS)
pfctl -a trenchcoat -F all 2>/dev/null || true
echo "Flushed pf anchor trenchcoat (if present)."
""",
            encoding="utf-8",
        )
        try:
            path.chmod(path.stat().st_mode | 0o111)
        except OSError:
            pass

    def _disarm_darwin(self) -> None:
        self._run(["pfctl", "-a", "trenchcoat", "-F", "all"])
