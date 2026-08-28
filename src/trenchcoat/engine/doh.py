"""DNS-over-HTTPS via the cloak chain (Phase 2)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Sequence

import httpx

log = logging.getLogger("trenchcoat.doh")

DEFAULT_DOH = "https://cloudflare-dns.com/dns-query"


@dataclass
class DohResult:
    name: str
    answers: list[str]
    via_proxy: str | None
    error: str | None = None


async def resolve_doh(
    name: str,
    proxy_urls: Sequence[str] | None = None,
    doh_url: str = DEFAULT_DOH,
    timeout: float = 20.0,
) -> DohResult:
    """
    Resolve A records using DoH JSON API, optionally through the last hop proxy.
    """
    proxy = proxy_urls[-1] if proxy_urls else None
    headers = {"accept": "application/dns-json"}
    params = {"name": name, "type": "A"}
    try:
        async with httpx.AsyncClient(proxy=proxy, timeout=timeout) as client:
            r = await client.get(doh_url, headers=headers, params=params)
            r.raise_for_status()
            data = r.json()
            answers = [a.get("data", "") for a in data.get("Answer", []) if a.get("type") == 1]
            return DohResult(name=name, answers=answers, via_proxy=proxy)
    except Exception as exc:  # noqa: BLE001
        log.debug("DoH failed: %s", exc)
        return DohResult(name=name, answers=[], via_proxy=proxy, error=str(exc))
