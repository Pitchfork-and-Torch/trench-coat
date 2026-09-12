"""Core cloak engine — orchestrates chain, proxy entry, kill-switch, health."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any

from trenchcoat.config.models import AppConfig, ChainConfig
from trenchcoat.engine.chain import ChainBuilder, ChainRotator, ChainSnapshot
from trenchcoat.engine.decoy import DecoyGenerator
from trenchcoat.engine.dns_guard import DnsGuard
from trenchcoat.engine.killswitch import KillSwitch, KillSwitchState
from trenchcoat.engine.proxy_server import ChainProxyServer
from trenchcoat.engine.split_tunnel import SplitTunnelEngine
from trenchcoat.engine.status_bus import clear_status, write_status
from trenchcoat.engine.tor_control import signal_newnym

log = logging.getLogger("trenchcoat.engine")


@dataclass
class EngineStatus:
    running: bool = False
    chain_name: str | None = None
    profile: str | None = None
    listen: str | None = None
    proxy_chain: list[str] = field(default_factory=list)
    snapshot: ChainSnapshot | None = None
    kill_switch: KillSwitchState | None = None
    bytes_in: int = 0
    bytes_out: int = 0
    connections: int = 0
    active_connections: int = 0
    bypass_count: int = 0
    refused_connects: int = 0
    decoy_sent: int = 0
    started_at: float | None = None
    messages: list[str] = field(default_factory=list)
    dns_recommendations: list[str] = field(default_factory=list)
    split_rules: int = 0
    fail_closed_tripped: bool = False
    refuse_direct: bool = True

    def to_dict(self) -> dict[str, Any]:
        snap = None
        if self.snapshot:
            snap = {
                "name": self.snapshot.name,
                "profile": self.snapshot.profile,
                "healthy": self.snapshot.healthy,
                "total_latency_ms": self.snapshot.total_latency_ms,
                "message": self.snapshot.message,
                "hops": [
                    {
                        "id": h.hop_id,
                        "health": h.health.value,
                        "latency_ms": h.latency_ms,
                        "error": h.error,
                    }
                    for h in self.snapshot.hops
                ],
            }
        return {
            "running": self.running,
            "chain_name": self.chain_name,
            "profile": self.profile,
            "listen": self.listen,
            "proxy_chain": self.proxy_chain,
            "snapshot": snap,
            "bytes_in": self.bytes_in,
            "bytes_out": self.bytes_out,
            "connections": self.connections,
            "active_connections": self.active_connections,
            "bypass_count": self.bypass_count,
            "refused_connects": self.refused_connects,
            "decoy_sent": self.decoy_sent,
            "split_rules": self.split_rules,
            "started_at": self.started_at,
            "messages": self.messages,
            "dns_recommendations": self.dns_recommendations,
            "kill_switch_active": bool(self.kill_switch and self.kill_switch.active),
            "fail_closed_tripped": self.fail_closed_tripped,
            "refuse_direct": self.refuse_direct,
        }


class CloakEngine:
    def __init__(self, app_config: AppConfig, chain: ChainConfig) -> None:
        self.app_config = app_config
        self.chain = chain
        self.builder = ChainBuilder(chain)
        self.rotator = ChainRotator(self.builder, on_rotate=self._on_rotate)
        self.killswitch = KillSwitch(strict=chain.policy.strict_kill_switch)
        self.dns = DnsGuard()
        self.split = SplitTunnelEngine(chain.split_tunnel)
        self.decoy = DecoyGenerator(
            interval_seconds=float(chain.policy.decoy_interval_seconds),
        )
        self.proxy: ChainProxyServer | None = None
        self._status = EngineStatus()
        self._health_task: asyncio.Task[None] | None = None
        self._stop = asyncio.Event()
        self._last_probe_at: float = 0.0

    @property
    def status(self) -> EngineStatus:
        if self.proxy:
            self._status.bytes_in = self.proxy.bytes_in
            self._status.bytes_out = self.proxy.bytes_out
            self._status.connections = self.proxy.connections
            self._status.active_connections = self.proxy.active
            self._status.bypass_count = self.proxy.bypass_count
            self._status.refused_connects = self.proxy.refused_connects
            self._status.refuse_direct = self.proxy.refuse_direct
        self._status.decoy_sent = self.decoy.stats.sent
        self._status.split_rules = len(self.split.rules)
        return self._status

    def _publish(self) -> None:
        try:
            write_status(self.status.to_dict())
        except Exception as exc:  # noqa: BLE001
            log.debug("status bus write failed: %s", exc)

    def _apply_urls(self, urls: list[str]) -> None:
        """Update live proxy chain and fail-closed refuse mode."""
        self._status.proxy_chain = urls
        if self.proxy:
            self.proxy.update_chain(urls)
            # Always refuse direct when fail_closed policy is on; empty chain then holds the line.
            self.proxy.set_refuse_direct(self.chain.policy.fail_closed)
            self.proxy.allow_partial_chain = self.chain.policy.allow_partial_chain
        self.decoy.update_proxies(urls)

        if self.chain.policy.fail_closed and not urls:
            if not self._status.fail_closed_tripped:
                log.error("all hops dead — fail-closed: refusing CONNECTs (no clearnet)")
                self._status.messages.append(
                    "ALERT: all hops dead. Fail-closed holding the line — no clearnet via cloak."
                )
            self._status.fail_closed_tripped = True
            self._status.refuse_direct = True
        else:
            if self._status.fail_closed_tripped and urls:
                self._status.messages.append("Chain recovered — hops live again.")
                log.info("chain recovered with %d hop URL(s)", len(urls))
            self._status.fail_closed_tripped = False
            self._status.refuse_direct = self.chain.policy.fail_closed

    def _on_rotate(self, snap: ChainSnapshot) -> None:
        self._status.snapshot = snap
        urls = self.builder.proxy_urls()
        self._apply_urls(urls)
        # Best-effort Tor circuit rebuild
        try:
            asyncio.get_running_loop().create_task(self._maybe_newnym())
        except RuntimeError:
            pass
        log.info("rotation complete healthy=%s", snap.healthy)

    async def _maybe_newnym(self) -> None:
        ctrl = 9051
        for hop in self.chain.hops:
            if hop.type.value == "tor":
                ctrl = int(hop.options.get("control_port", 9051))
                break
        ok, msg = await signal_newnym(port=ctrl)
        if ok:
            self._status.messages.append("Tor NEWNYM signalled (new circuit).")
            log.info("NEWNYM ok: %s", msg)
        else:
            log.debug("NEWNYM skipped: %s", msg)

    async def start(self) -> EngineStatus:
        self._stop.clear()
        self._status.messages.clear()
        self._status.fail_closed_tripped = False
        self._status.chain_name = self.chain.name
        self._status.profile = self.chain.profile.value
        self._status.refuse_direct = self.chain.policy.fail_closed

        snap = await self.builder.build()
        self._status.snapshot = snap
        urls = self.builder.proxy_urls()
        self._status.proxy_chain = urls

        if self.chain.policy.fail_closed and not urls:
            self._status.running = False
            self._status.messages.append(
                "FAIL-CLOSED: no live hops. Cloak not engaged. Configure hops or start Tor."
            )
            # Still allow dry listen? No — fail closed.
            return self.status

        self.proxy = ChainProxyServer(
            self.app_config.listen_host,
            self.app_config.listen_port,
            urls,
            split_tunnel=self.split,
            refuse_direct=self.chain.policy.fail_closed,
            allow_partial_chain=self.chain.policy.allow_partial_chain,
        )
        await self.proxy.start()
        self._status.listen = f"{self.app_config.listen_host}:{self.app_config.listen_port}"
        self._status.running = True
        self._status.started_at = time.time()
        self._status.split_rules = len(self.split.rules)
        self._last_probe_at = time.time()

        if self.chain.policy.kill_switch:
            ks = self.killswitch.arm(allow_uid_ports=[self.app_config.listen_port])
            self._status.kill_switch = ks
            self._status.messages.extend(ks.messages)
            # Soft kill-switch = refuse direct at SOCKS layer (already refuse_direct from fail_closed).
            if self.proxy and self.chain.policy.strict_kill_switch:
                self.proxy.set_refuse_direct(True)
                self._status.refuse_direct = True

        dns_report = self.dns.audit()
        self._status.dns_recommendations = dns_report.recommendations
        if self.split.rules:
            self._status.messages.append(
                f"Split-tunnel: {len(self.split.rules)} rule(s) active (CIDR/domain/process)."
            )

        self.decoy.update_proxies(urls)
        if self.chain.policy.decoy_traffic:
            await self.decoy.start()
            self._status.messages.append(
                f"Decoy traffic on (~every {self.chain.policy.decoy_interval_seconds}s)."
            )

        await self.rotator.start()
        self._health_task = asyncio.create_task(self._health_loop(), name="health")
        self._status.messages.append(
            f"Cloak engaged: {self.chain.name} ({self.chain.profile.value}). "
            f"Point apps at socks5://{self._status.listen}"
        )
        self._publish()
        return self.status

    async def stop(self) -> EngineStatus:
        self._stop.set()
        await self.rotator.stop()
        await self.decoy.stop()
        if self._health_task:
            self._health_task.cancel()
            try:
                await self._health_task
            except asyncio.CancelledError:
                pass
        if self.proxy:
            await self.proxy.stop()
            self.proxy = None
        if self.chain.policy.kill_switch:
            self._status.kill_switch = self.killswitch.disarm()
        try:
            from trenchcoat.hops.process_manager import MANAGER

            MANAGER.stop_all()
        except Exception:  # noqa: BLE001
            pass
        self._status.running = False
        self._status.fail_closed_tripped = False
        self._status.messages.append("Cloak disengaged. You are visible again.")
        clear_status()
        return self.status

    async def _health_loop(self) -> None:
        interval = float(self.chain.policy.health_check_seconds)
        # Heartbeat often; full hop rebuild on elapsed interval (not wall-clock modulo).
        heartbeat = min(interval, 5.0)
        while not self._stop.is_set():
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=heartbeat)
                break
            except TimeoutError:
                self._publish()
                now = time.time()
                if now - self._last_probe_at < interval:
                    continue
                self._last_probe_at = now
                snap = await self.builder.build()
                self._status.snapshot = snap
                urls = self.builder.proxy_urls()
                self._apply_urls(urls)
                self._publish()
