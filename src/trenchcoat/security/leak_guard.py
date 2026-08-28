"""Anti-leak checklist and session hygiene."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LeakCheck:
    id: str
    title: str
    status: str  # pass | warn | fail | info
    detail: str


def run_leak_checklist(proxy_active: bool, ipv6_enabled: bool | None, kill_switch: bool) -> list[LeakCheck]:
    checks = [
        LeakCheck(
            id="proxy",
            title="Cloak entry active",
            status="pass" if proxy_active else "fail",
            detail="Local SOCKS entry is listening" if proxy_active else "No local cloak listener",
        ),
        LeakCheck(
            id="killswitch",
            title="Kill-switch",
            status="pass" if kill_switch else "warn",
            detail="Kill-switch armed" if kill_switch else "Kill-switch off — traffic may leak on failure",
        ),
        LeakCheck(
            id="ipv6",
            title="IPv6 exposure",
            status="warn" if ipv6_enabled else "pass",
            detail=(
                "IPv6 appears available — disable or tunnel it"
                if ipv6_enabled
                else "IPv6 not obviously available"
            ),
        ),
        LeakCheck(
            id="webrtc",
            title="WebRTC",
            status="info",
            detail="Disable WebRTC in browser or use containers; OS tool cannot fully suppress browser leaks.",
        ),
        LeakCheck(
            id="dns",
            title="DNS",
            status="info",
            detail="Use proxy-aware DNS or VPN DNS. Avoid ISP resolvers while cloaked.",
        ),
        LeakCheck(
            id="fingerprint",
            title="Browser fingerprint",
            status="info",
            detail="Prefer hardened browser profile; canvas/WebGL spoofing is browser-side (Phase 2 extension).",
        ),
    ]
    return checks
