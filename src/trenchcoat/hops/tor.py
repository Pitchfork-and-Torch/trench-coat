"""Tor hop — local SOCKS with bootstrap awareness."""

from __future__ import annotations

import asyncio
import time

from trenchcoat.hops.base import HopHealth, HopStatus
from trenchcoat.hops.socks5 import Socks5Hop


class TorHop(Socks5Hop):
    """Tor is SOCKS5; we add friendly messaging and optional control-port hooks."""

    async def probe(self, timeout: float = 8.0) -> HopStatus:
        status = await super().probe(timeout=timeout)
        if status.health == HopHealth.DEAD:
            hint = (
                "Tor SOCKS unreachable. Start Tor (tor service / Tor Browser) "
                f"and ensure SOCKS listens on {self.config.host}:{self.config.port}."
            )
            status.error = f"{status.error}; {hint}" if status.error else hint
            self.status = status
        return status

    async def newnym_hint(self) -> str:
        """Return instructions for NEWNYM (circuit rebuild) via control port."""
        ctrl = self.config.options.get("control_port", 9051)
        return (
            f"Signal NEWNYM via Tor control port {ctrl} "
            "(authenticate with cookie/password). Full control-port integration: Phase 2."
        )

    async def wait_bootstrap(self, timeout: float = 60.0) -> bool:
        deadline = time.time() + timeout
        while time.time() < deadline:
            st = await self.probe(timeout=3.0)
            if st.health in (HopHealth.HEALTHY, HopHealth.DEGRADED):
                return True
            await asyncio.sleep(2.0)
        return False
