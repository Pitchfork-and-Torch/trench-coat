"""Egress identity checks (IsTor, public IP) through a proxy chain."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Sequence

import httpx

log = logging.getLogger("trenchcoat.identity")

TOR_CHECK_URL = "https://check.torproject.org/api/ip"
CF_TRACE_URL = "https://1.1.1.1/cdn-cgi/trace"


@dataclass
class IdentityReport:
    is_tor: bool | None
    ip: str | None
    via_proxy: str | None
    raw_tor_check: dict | None
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            "is_tor": self.is_tor,
            "ip": self.ip,
            "via_proxy": self.via_proxy,
            "error": self.error,
            "raw": self.raw_tor_check,
        }


async def check_identity(
    proxy_urls: Sequence[str] | None = None,
    timeout: float = 45.0,
) -> IdentityReport:
    """
    Fetch public identity. If proxy_urls provided, use the last hop URL
    (egress) or first available socks/http proxy string.
    """
    proxy = None
    if proxy_urls:
        proxy = proxy_urls[-1] if proxy_urls else None

    try:
        async with httpx.AsyncClient(proxy=proxy, timeout=timeout, follow_redirects=True) as client:
            r = await client.get(TOR_CHECK_URL)
            r.raise_for_status()
            data = r.json()
            return IdentityReport(
                is_tor=bool(data.get("IsTor")),
                ip=data.get("IP"),
                via_proxy=proxy,
                raw_tor_check=data,
            )
    except Exception as exc:  # noqa: BLE001
        log.debug("tor check failed: %s", exc)
        # Fallback: CF trace for IP only
        try:
            async with httpx.AsyncClient(proxy=proxy, timeout=timeout) as client:
                t = await client.get(CF_TRACE_URL)
                ip = None
                for line in t.text.splitlines():
                    if line.startswith("ip="):
                        ip = line.split("=", 1)[1]
                        break
                return IdentityReport(
                    is_tor=None,
                    ip=ip,
                    via_proxy=proxy,
                    raw_tor_check=None,
                    error=f"torproject check failed: {exc}",
                )
        except Exception as exc2:  # noqa: BLE001
            return IdentityReport(
                is_tor=None,
                ip=None,
                via_proxy=proxy,
                raw_tor_check=None,
                error=str(exc2),
            )
