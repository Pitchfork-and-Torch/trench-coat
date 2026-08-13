"""Abstract hop interface."""

from __future__ import annotations

import abc
import time
from dataclasses import dataclass, field
from enum import Enum

from trenchcoat.config.models import HopConfig, HopType


class HopHealth(str, Enum):
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DEAD = "dead"


@dataclass
class HopStatus:
    hop_id: str
    health: HopHealth = HopHealth.UNKNOWN
    latency_ms: float | None = None
    last_check: float = field(default_factory=time.time)
    error: str | None = None
    bytes_in: int = 0
    bytes_out: int = 0


class Hop(abc.ABC):
    """A single layer of the trench coat."""

    def __init__(self, config: HopConfig) -> None:
        self.config = config
        self.status = HopStatus(hop_id=config.id)

    @property
    def hop_type(self) -> HopType:
        return self.config.type

    @property
    def is_local_socks_compatible(self) -> bool:
        """True if this hop exposes a SOCKS5 endpoint we can chain through."""
        return self.config.type in {
            HopType.SOCKS5,
            HopType.TOR,
            HopType.RESIDENTIAL,
            HopType.SELF_HOSTED,
            HopType.HTTP,
            HopType.HTTPS,
        }

    @abc.abstractmethod
    async def probe(self, timeout: float = 5.0) -> HopStatus:
        """Health-check this hop."""

    def as_proxy_url(self) -> str | None:
        """Return a python-socks / httpx compatible proxy URL if applicable."""
        cfg = self.config
        auth = ""
        if cfg.username:
            pw = cfg.password or ""
            auth = f"{cfg.username}:{pw}@"
        # Prefer explicit socks_bridge for managed L3/PT hops
        if cfg.options.get("socks_bridge"):
            host, _, port_s = str(cfg.options["socks_bridge"]).partition(":")
            return f"socks5://{auth}{host or '127.0.0.1'}:{port_s or 1080}"
        scheme = {
            HopType.SOCKS5: "socks5",
            HopType.TOR: "socks5",
            HopType.RESIDENTIAL: "socks5",
            HopType.SELF_HOSTED: "socks5",
            HopType.SHADOWSOCKS: "socks5",
            HopType.HYSTERIA2: "socks5",
            HopType.BRIDGE: "socks5",
            HopType.HTTP: "http",
            HopType.HTTPS: "http",
        }.get(cfg.type)
        if not scheme:
            return None
        return f"{scheme}://{auth}{cfg.host}:{cfg.port}"


def hop_from_config(config: HopConfig) -> Hop:
    from trenchcoat.hops.socks5 import Socks5Hop
    from trenchcoat.hops.http_proxy import HttpProxyHop
    from trenchcoat.hops.tor import TorHop
    from trenchcoat.hops.stub import StubHop
    from trenchcoat.hops.managed import (
        BridgeHop,
        Hysteria2Hop,
        ShadowsocksHop,
        WireGuardHop,
        managed_hop_from_config,
    )

    # options.transport forces bridge driver
    managed = managed_hop_from_config(config)
    if managed is not None:
        return managed

    mapping = {
        HopType.SOCKS5: Socks5Hop,
        HopType.RESIDENTIAL: Socks5Hop,
        HopType.SELF_HOSTED: Socks5Hop,
        HopType.HTTP: HttpProxyHop,
        HopType.HTTPS: HttpProxyHop,
        HopType.TOR: TorHop,
        HopType.I2P: StubHop,
        HopType.SHADOWSOCKS: ShadowsocksHop,
        HopType.WIREGUARD: WireGuardHop,
        HopType.HYSTERIA2: Hysteria2Hop,
        HopType.BRIDGE: BridgeHop,
    }
    cls = mapping.get(config.type, StubHop)
    return cls(config)
