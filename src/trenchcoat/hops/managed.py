"""Managed hops: WireGuard, Shadowsocks, Hysteria2, bridges via external binaries."""

from __future__ import annotations

import time

from trenchcoat.config.models import HopConfig, HopType
from trenchcoat.hops.base import Hop, HopHealth, HopStatus
from trenchcoat.hops.process_manager import MANAGER, resolve_binary, wait_port
from trenchcoat.hops.socks5 import Socks5Hop


class ManagedSocksHop(Hop):
    """
    Base for hops that launch an external client exposing a local SOCKS bridge.

    options:
      socks_bridge: host:port (default 127.0.0.1:<config.port>)
      binary: path to executable
      args: extra CLI args list
      auto_start: bool (default True)
      conf / config: config file path
    """

    binary_names: tuple[str, ...] = ()
    default_bridge_port: int = 1080

    async def ensure_started(self) -> str | None:
        """Return error message or None."""
        opts = self.config.options
        if opts.get("auto_start", True) is False:
            return None
        bridge = self._bridge()
        host, port = bridge
        # already up?
        if await wait_port(host, port, timeout=0.5):
            return None
        cmd = self.build_command()
        if not cmd:
            return (
                f"No binary for {self.config.type.value}. Install client or set options.binary / socks_bridge."
            )
        try:
            MANAGER.start(self.config.id, cmd)
        except Exception as exc:  # noqa: BLE001
            return str(exc)
        ok = await wait_port(host, port, timeout=float(opts.get("start_timeout", 25)))
        if not ok:
            return f"Process started but SOCKS {host}:{port} not ready"
        return None

    def build_command(self) -> list[str] | None:
        raise NotImplementedError

    def _bridge(self) -> tuple[str, int]:
        opts = self.config.options
        raw = opts.get("socks_bridge")
        if raw:
            host, _, port_s = str(raw).partition(":")
            return host or "127.0.0.1", int(port_s or self.default_bridge_port)
        return "127.0.0.1", int(opts.get("local_port") or self.config.port or self.default_bridge_port)

    def as_proxy_url(self) -> str | None:
        host, port = self._bridge()
        auth = ""
        if self.config.username:
            auth = f"{self.config.username}:{self.config.password or ''}@"
        return f"socks5://{auth}{host}:{port}"

    async def probe(self, timeout: float = 5.0) -> HopStatus:
        err = await self.ensure_started()
        host, port = self._bridge()
        bridge_cfg = HopConfig(
            id=f"{self.config.id}-bridge",
            type=HopType.SOCKS5,
            host=host,
            port=port,
            username=self.config.username,
            password=self.config.password,
        )
        if err:
            # still try probe in case user started externally
            st = await Socks5Hop(bridge_cfg).probe(timeout=timeout)
            if st.health == HopHealth.DEAD:
                st.error = err
                st.health = HopHealth.UNKNOWN if "No binary" in err else HopHealth.DEAD
            self.status = st
            return st
        st = await Socks5Hop(bridge_cfg).probe(timeout=timeout)
        self.status = st
        return st


class ShadowsocksHop(ManagedSocksHop):
    binary_names = ("sslocal", "ss-local")
    default_bridge_port = 1080

    def build_command(self) -> list[str] | None:
        opts = self.config.options
        binary = resolve_binary(opts, "binary", *self.binary_names)
        if not binary:
            return None
        host, port = self._bridge()
        conf = opts.get("conf") or opts.get("config")
        if conf:
            return [binary, "-c", str(conf)]
        # sslocal -s server -p port -l local -k password -m method
        method = opts.get("method", "chacha20-ietf-poly1305")
        password = self.config.password or opts.get("password") or ""
        return [
            binary,
            "-s",
            self.config.host,
            "-p",
            str(opts.get("server_port") or self.config.port),
            "-l",
            str(port),
            "-k",
            password,
            "-m",
            method,
            "--local-addr",
            host,
        ]


class Hysteria2Hop(ManagedSocksHop):
    binary_names = ("hysteria", "hysteria2", "hy2")
    default_bridge_port = 1080

    def build_command(self) -> list[str] | None:
        opts = self.config.options
        binary = resolve_binary(opts, "binary", *self.binary_names)
        if not binary:
            return None
        conf = opts.get("conf") or opts.get("config")
        if conf:
            return [binary, "client", "-c", str(conf)]
        # bare server URL mode when supported
        server = opts.get("server") or f"{self.config.host}:{self.config.port}"
        host, port = self._bridge()
        return [
            binary,
            "client",
            "--server",
            str(server),
            "--socks5",
            f"{host}:{port}",
        ]


class WireGuardHop(ManagedSocksHop):
    """
    WireGuard itself is L3; we expect a userspace socks bridge (e.g. tun2socks)
    or pre-up interface. options:
      conf: wg conf path
      socks_bridge: required for chain participation
      up_cmd: custom command list
    """

    binary_names = ("wg-quick", "wireguard-go", "wg")
    default_bridge_port = 1080

    def build_command(self) -> list[str] | None:
        opts = self.config.options
        if opts.get("up_cmd"):
            return list(opts["up_cmd"])
        conf = opts.get("conf") or opts.get("config")
        binary = resolve_binary(opts, "binary", "wg-quick")
        if binary and conf:
            return [binary, "up", str(conf)]
        return None

    async def probe(self, timeout: float = 5.0) -> HopStatus:
        opts = self.config.options
        if not opts.get("socks_bridge"):
            # try ensure start for interface only
            if opts.get("auto_start", False):
                await self.ensure_started()
            self.status = HopStatus(
                hop_id=self.config.id,
                health=HopHealth.UNKNOWN,
                last_check=time.time(),
                error=(
                    "WireGuard is L3. Set options.socks_bridge to a local SOCKS "
                    "(e.g. tun2socks) after the tunnel is up."
                ),
            )
            return self.status
        return await super().probe(timeout=timeout)


class BridgeHop(ManagedSocksHop):
    """obfs4 / snowflake / meek via lyrebird or tor PTs."""

    binary_names = ("lyrebird", "obfs4proxy", "snowflake-client")
    default_bridge_port = 9050

    def build_command(self) -> list[str] | None:
        # PTs are normally driven by Tor; if user provides a bridge socks already, skip
        opts = self.config.options
        if opts.get("socks_bridge"):
            return None
        binary = resolve_binary(opts, "binary", *self.binary_names)
        conf = opts.get("conf") or opts.get("torrc")
        if binary and conf:
            return [binary, "-enableLogging", "-logLevel", "INFO"]  # minimal; prefer tor managed
        return None

    async def probe(self, timeout: float = 5.0) -> HopStatus:
        opts = self.config.options
        transport = opts.get("transport", "obfs4")
        if not opts.get("socks_bridge") and not opts.get("conf"):
            self.status = HopStatus(
                hop_id=self.config.id,
                health=HopHealth.UNKNOWN,
                last_check=time.time(),
                error=(
                    f"Bridge transport '{transport}': point socks_bridge at Tor+PT SOCKS "
                    "or set conf for client binary."
                ),
            )
            return self.status
        return await super().probe(timeout=timeout)


def managed_hop_from_config(config: HopConfig) -> Hop | None:
    mapping: dict[HopType, type[ManagedSocksHop]] = {
        HopType.SHADOWSOCKS: ShadowsocksHop,
        HopType.HYSTERIA2: Hysteria2Hop,
        HopType.WIREGUARD: WireGuardHop,
    }
    # bridge via options.transport on self_hosted or explicit
    if config.options.get("transport") in ("obfs4", "snowflake", "meek", "meek_lite", "webtunnel"):
        return BridgeHop(config)
    cls = mapping.get(config.type)
    return cls(config) if cls else None
