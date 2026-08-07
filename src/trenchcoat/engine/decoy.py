"""Decoy traffic generator — rate-limited, plausible HTTPS noise (Phase 3)."""

from __future__ import annotations

import asyncio
import logging
import random
import time
from dataclasses import dataclass
from typing import Sequence

import httpx

log = logging.getLogger("trenchcoat.decoy")

# Benign endpoints commonly used for connectivity checks
DECOY_URLS = (
    "https://www.google.com/generate_204",
    "https://www.gstatic.com/generate_204",
    "https://cloudflare.com/cdn-cgi/trace",
    "https://example.com/",
)


@dataclass
class DecoyStats:
    sent: int = 0
    errors: int = 0
    last_url: str | None = None
    last_ms: float | None = None
    running: bool = False


class DecoyGenerator:
    def __init__(
        self,
        proxy_urls: Sequence[str] | None = None,
        interval_seconds: float = 60.0,
        jitter: float = 0.35,
    ) -> None:
        self.proxy_urls = list(proxy_urls or [])
        self.interval = max(15.0, interval_seconds)
        self.jitter = jitter
        self.stats = DecoyStats()
        self._task: asyncio.Task[None] | None = None
        self._stop = asyncio.Event()

    def update_proxies(self, proxy_urls: Sequence[str]) -> None:
        self.proxy_urls = list(proxy_urls)

    async def start(self) -> None:
        if self._task:
            return
        self._stop.clear()
        self.stats.running = True
        self._task = asyncio.create_task(self._loop(), name="decoy-traffic")

    async def stop(self) -> None:
        self._stop.set()
        self.stats.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _loop(self) -> None:
        while not self._stop.is_set():
            await self.pulse()
            delay = self.interval * (1.0 + random.uniform(-self.jitter, self.jitter))
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=max(5.0, delay))
                break
            except TimeoutError:
                continue

    async def pulse(self) -> None:
        url = random.choice(DECOY_URLS)
        proxy = self.proxy_urls[-1] if self.proxy_urls else None
        start = time.perf_counter()
        try:
            async with httpx.AsyncClient(proxy=proxy, timeout=25.0, follow_redirects=True) as client:
                await client.get(url)
            self.stats.sent += 1
            self.stats.last_url = url
            self.stats.last_ms = round((time.perf_counter() - start) * 1000, 1)
            log.debug("decoy ok %s via %s", url, proxy)
        except Exception as exc:  # noqa: BLE001
            self.stats.errors += 1
            self.stats.last_url = url
            log.debug("decoy fail %s: %s", url, exc)
