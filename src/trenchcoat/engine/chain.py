"""Dynamic multi-hop chain builder, health, rotation, and path selection."""

from __future__ import annotations

import asyncio
import logging
import random
import time
from dataclasses import dataclass, field
from typing import Callable

from trenchcoat.config.models import ChainConfig, HopConfig
from trenchcoat.hops.base import Hop, HopHealth, HopStatus, hop_from_config

log = logging.getLogger("trenchcoat.chain")


@dataclass
class ChainSnapshot:
    name: str
    profile: str
    hops: list[HopStatus]
    healthy: bool
    built_at: float = field(default_factory=time.time)
    total_latency_ms: float | None = None
    message: str = ""


class ChainBuilder:
    """Construct and maintain an ordered list of live hops."""

    def __init__(self, chain: ChainConfig) -> None:
        self.chain = chain
        self._hops: list[Hop] = []
        self._lock = asyncio.Lock()
        self.last_snapshot: ChainSnapshot | None = None

    @property
    def hops(self) -> list[Hop]:
        return list(self._hops)

    def _instantiate(self, configs: list[HopConfig]) -> list[Hop]:
        return [hop_from_config(c) for c in configs if c.enabled]

    async def build(self) -> ChainSnapshot:
        async with self._lock:
            candidates = self.chain.active_hops()
            if self.chain.policy.randomize_order and len(candidates) > 2:
                # Keep first (entry) and last (often Tor exit) stable when possible
                mid = candidates[1:-1]
                random.shuffle(mid)
                candidates = [candidates[0], *mid, candidates[-1]] if len(candidates) > 1 else candidates

            hops = self._instantiate(candidates)
            # Probe all hops concurrently — doctor and rebuilds stay snappy
            probe_results = await asyncio.gather(
                *[hop.probe() for hop in hops],
                return_exceptions=True,
            )
            statuses: list[HopStatus] = []
            for hop, result in zip(hops, probe_results, strict=True):
                if isinstance(result, BaseException):
                    st = HopStatus(
                        hop_id=hop.config.id,
                        health=HopHealth.DEAD,
                        error=str(result),
                    )
                    hop.status = st
                else:
                    st = result
                statuses.append(st)
                log.info("hop %s → %s (%s ms)", hop.config.id, st.health.value, st.latency_ms)

            live = [
                h
                for h, s in zip(hops, statuses, strict=True)
                if s.health in (HopHealth.HEALTHY, HopHealth.DEGRADED)
            ]
            # Stub/UNKNOWN hops with socks_bridge may still be useful — exclude DEAD only for min check
            dead = [s for s in statuses if s.health == HopHealth.DEAD]
            min_hops = self.chain.policy.min_hops
            # Count chainable hops (have proxy URL)
            chainable = [h for h in live if h.as_proxy_url()]
            healthy = len(chainable) >= min(min_hops, max(1, len([c for c in candidates if c.enabled])))
            # If nothing is up but we only have stubs configured, report degraded not fatal for dry-run
            if not candidates:
                healthy = False

            latencies = [s.latency_ms for s in statuses if s.latency_ms is not None]
            total = sum(latencies) if latencies else None

            # Only keep live chainable hops — never expose dead endpoints as usable
            self._hops = chainable
            msg = ""
            if dead:
                msg = f"{len(dead)} hop(s) dead; chain may be incomplete."
            if not chainable:
                msg = (
                    "No live SOCKS/HTTP hops detected. Configure hop endpoints "
                    "(e.g. start Tor on 9050) or run `trench doctor`."
                )
                healthy = False

            snap = ChainSnapshot(
                name=self.chain.name,
                profile=self.chain.profile.value,
                hops=statuses,
                healthy=healthy,
                total_latency_ms=total,
                message=msg,
            )
            self.last_snapshot = snap
            return snap

    def proxy_urls(self) -> list[str]:
        urls: list[str] = []
        for hop in self._hops:
            url = hop.as_proxy_url()
            if url:
                urls.append(url)
        return urls

    def primary_proxy_url(self) -> str | None:
        """
        For MVP single-listener mode we expose the first hop as the entry
        when only one hop works; multi-hop CONNECT chaining uses chain_proxy().
        """
        urls = self.proxy_urls()
        return urls[0] if urls else None


class ChainRotator:
    """Periodically rebuild circuits / rotate mid-hops."""

    def __init__(
        self,
        builder: ChainBuilder,
        on_rotate: Callable[[ChainSnapshot], None] | None = None,
    ) -> None:
        self.builder = builder
        self.on_rotate = on_rotate
        self._task: asyncio.Task[None] | None = None
        self._stop = asyncio.Event()

    async def start(self) -> None:
        minutes = self.builder.chain.policy.rotation_minutes
        if minutes <= 0:
            log.info("rotation disabled for chain %s", self.builder.chain.name)
            return
        self._stop.clear()
        self._task = asyncio.create_task(self._loop(minutes * 60), name="chain-rotator")

    async def stop(self) -> None:
        self._stop.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _loop(self, interval: float) -> None:
        while not self._stop.is_set():
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=interval)
                break
            except TimeoutError:
                log.info("rotating chain %s …", self.builder.chain.name)
                snap = await self.builder.build()
                if self.on_rotate:
                    self.on_rotate(snap)
