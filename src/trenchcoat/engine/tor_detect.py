"""Detect and wait for local Tor SOCKS endpoints."""

from __future__ import annotations

import asyncio
import socket
from dataclasses import dataclass


# Tor Browser default first; system tor second
DEFAULT_TOR_PORTS = (9150, 9050)


@dataclass
class TorEndpoint:
    host: str
    port: int

    def as_url(self) -> str:
        return f"socks5://{self.host}:{self.port}"

    def label(self) -> str:
        kind = "Tor Browser" if self.port == 9150 else "Tor"
        return f"{kind} SOCKS {self.host}:{self.port}"


def port_open(host: str, port: int, timeout: float = 0.4) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def detect_tor(host: str = "127.0.0.1", ports: tuple[int, ...] = DEFAULT_TOR_PORTS) -> TorEndpoint | None:
    for port in ports:
        if port_open(host, port):
            return TorEndpoint(host=host, port=port)
    return None


async def wait_for_tor(
    host: str = "127.0.0.1",
    ports: tuple[int, ...] = DEFAULT_TOR_PORTS,
    timeout: float = 90.0,
    interval: float = 1.5,
) -> TorEndpoint | None:
    """Poll until a Tor SOCKS port accepts connections or timeout."""
    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < deadline:
        found = detect_tor(host, ports)
        if found:
            return found
        await asyncio.sleep(interval)
    return None


def bind_chain_to_tor(chain_hops: list, endpoint: TorEndpoint) -> int:
    """
    Update tor-typed hops (and 127.0.0.1:9050/9150 placeholders) to live endpoint.
    Returns number of hops rewritten.
    """
    from trenchcoat.config.models import HopType

    n = 0
    for hop in chain_hops:
        is_tor = hop.type == HopType.TOR
        is_local_socks_placeholder = (
            hop.host in ("127.0.0.1", "localhost")
            and hop.port in DEFAULT_TOR_PORTS
            and hop.type in (HopType.TOR, HopType.SOCKS5)
        )
        if is_tor or is_local_socks_placeholder:
            hop.host = endpoint.host
            hop.port = endpoint.port
            if is_tor:
                hop.label = hop.label or endpoint.label()
            n += 1
    return n
