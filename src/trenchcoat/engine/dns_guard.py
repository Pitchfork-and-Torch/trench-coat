"""DNS leak protection helpers and guidance."""

from __future__ import annotations

import logging
import platform
import socket
from dataclasses import dataclass, field

log = logging.getLogger("trenchcoat.dns")


@dataclass
class DnsGuardReport:
    system: str = field(default_factory=platform.system)
    ipv6_likely_enabled: bool | None = None
    recommendations: list[str] = field(default_factory=list)
    leaks_detected: list[str] = field(default_factory=list)


class DnsGuard:
    """Best-effort DNS / IPv6 hygiene checks for the cloak session."""

    def audit(self) -> DnsGuardReport:
        report = DnsGuardReport()
        report.recommendations.extend(
            [
                "Route DNS through the chain (proxy DNS or VPN-provided resolvers).",
                "Disable IPv6 at OS level when the chain is IPv4-only.",
                "Browser: disable WebRTC or use extension; prefer Firefox + uBlock.",
                "Never set system DNS to your ISP while the cloak is active.",
            ]
        )
        # crude IPv6 check
        try:
            socket.socket(socket.AF_INET6, socket.SOCK_DGRAM).close()
            report.ipv6_likely_enabled = True
            report.recommendations.append(
                "IPv6 sockets available — ensure IPv6 is blocked or also tunneled."
            )
        except OSError:
            report.ipv6_likely_enabled = False

        if report.system == "Windows":
            report.recommendations.append(
                "Windows: `Get-NetAdapterBinding -ComponentID ms_tcpip6` to inspect IPv6."
            )
        elif report.system == "Linux":
            report.recommendations.append(
                "Linux: sysctl net.ipv6.conf.all.disable_ipv6=1 (session hardening)."
            )
        return report

    def resolve_check(self, host: str = "example.com") -> str | None:
        try:
            infos = socket.getaddrinfo(host, 80, type=socket.SOCK_STREAM)
            return infos[0][4][0] if infos else None
        except OSError as exc:
            log.debug("resolve failed: %s", exc)
            return None
