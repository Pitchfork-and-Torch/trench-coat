"""Stub hops for protocols that require external daemons (WireGuard, SS, Hysteria2, I2P)."""

from __future__ import annotations

import time

from trenchcoat.hops.base import Hop, HopHealth, HopStatus


class StubHop(Hop):
    """
    Marks advanced hop types that need an external client process.

    MVP strategy: user runs the native client (wg-quick, sslocal, hysteria, i2pd)
    which exposes a local SOCKS/HTTP listener; replace the hop type with socks5
    pointing at that listener, or wait for Phase 2 native drivers.
    """

    async def probe(self, timeout: float = 5.0) -> HopStatus:
        _ = timeout
        self.status = HopStatus(
            hop_id=self.config.id,
            health=HopHealth.UNKNOWN,
            last_check=time.time(),
            error=(
                f"Hop type '{self.config.type.value}' is not natively driven in MVP. "
                "Run the external client and point a socks5 hop at its local listener, "
                "or enable this hop once a local SOCKS bridge is configured in options."
            ),
        )
        # If user provided a bridge_port, try treating as socks
        bridge = self.config.options.get("socks_bridge")
        if bridge:
            from trenchcoat.config.models import HopConfig, HopType
            from trenchcoat.hops.socks5 import Socks5Hop

            host, _, port_s = str(bridge).partition(":")
            bridge_cfg = HopConfig(
                id=f"{self.config.id}-bridge",
                type=HopType.SOCKS5,
                host=host or "127.0.0.1",
                port=int(port_s or "1080"),
                username=self.config.username,
                password=self.config.password,
            )
            return await Socks5Hop(bridge_cfg).probe()
        return self.status
