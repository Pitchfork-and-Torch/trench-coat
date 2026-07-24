"""
Local SOCKS5 entry that multi-hop chains outbound connections.

MVP chaining model:
  Client → Trench Coat (local SOCKS5) → hop1 → hop2 → … → destination

Uses python-socks for nested proxy chains when available.

Fail-closed contract:
  - When refuse_direct is True and the hop chain is empty, CONNECT is refused
    (never silent clearnet via the cloak entry).
  - Multi-hop failure does not fall back to first-hop-only unless
    allow_partial_chain is True.
"""

from __future__ import annotations

import asyncio
import logging
import struct
from typing import Sequence

from trenchcoat.engine.split_tunnel import SplitTunnelEngine

log = logging.getLogger("trenchcoat.proxy")


class DirectDialRefused(RuntimeError):
    """Raised when the cloak refuses a direct (clearnet) dial under fail-closed."""


class ChainProxyServer:
    def __init__(
        self,
        listen_host: str,
        listen_port: int,
        proxy_chain: Sequence[str],
        split_tunnel: SplitTunnelEngine | None = None,
        *,
        refuse_direct: bool = True,
        allow_partial_chain: bool = False,
    ) -> None:
        self.listen_host = listen_host
        self.listen_port = listen_port
        self.proxy_chain = list(proxy_chain)
        self.split_tunnel = split_tunnel or SplitTunnelEngine()
        self.refuse_direct = refuse_direct
        self.allow_partial_chain = allow_partial_chain
        self._server: asyncio.Server | None = None
        self.bytes_in = 0
        self.bytes_out = 0
        self.connections = 0
        self.active = 0
        self.bypass_count = 0
        self.refused_connects = 0

    def update_chain(self, proxy_chain: Sequence[str]) -> None:
        self.proxy_chain = list(proxy_chain)
        label = " → ".join(self.proxy_chain) if self.proxy_chain else "(empty — refuse_direct)" if self.refuse_direct else "(direct)"
        log.info("proxy chain updated: %s", label)

    def set_refuse_direct(self, refuse: bool) -> None:
        self.refuse_direct = refuse
        log.info("refuse_direct=%s", refuse)

    async def start(self) -> None:
        self._server = await asyncio.start_server(
            self._handle_client,
            self.listen_host,
            self.listen_port,
        )
        sockets = self._server.sockets or []
        addrs = ", ".join(str(s.getsockname()) for s in sockets)
        log.info("cloak entry listening on %s", addrs)

    async def stop(self) -> None:
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        self.connections += 1
        self.active += 1
        peer = writer.get_extra_info("peername")
        try:
            # SOCKS5 greeting
            header = await reader.readexactly(2)
            ver, nmethods = header[0], header[1]
            if ver != 5:
                writer.close()
                return
            await reader.readexactly(nmethods)
            writer.write(b"\x05\x00")  # no auth
            await writer.drain()

            # Request
            req = await reader.readexactly(4)
            if req[0] != 5 or req[1] != 1:  # CONNECT only
                writer.write(b"\x05\x07\x00\x01" + b"\x00" * 6)
                await writer.drain()
                return
            atyp = req[3]
            if atyp == 1:
                addr_raw = await reader.readexactly(4)
                host = ".".join(str(b) for b in addr_raw)
            elif atyp == 3:
                ln = (await reader.readexactly(1))[0]
                host = (await reader.readexactly(ln)).decode("utf-8", errors="replace")
            elif atyp == 4:
                addr_raw = await reader.readexactly(16)
                host = ":".join(f"{addr_raw[i]:02x}{addr_raw[i+1]:02x}" for i in range(0, 16, 2))
            else:
                writer.write(b"\x05\x08\x00\x01" + b"\x00" * 6)
                await writer.drain()
                return
            port = struct.unpack("!H", await reader.readexactly(2))[0]

            decision = self.split_tunnel.decide(host, port)
            if decision.bypass:
                # Split-tunnel exclude is intentional clearnet for matching destinations.
                # Under strict refuse_direct, still allow only explicit exclude rules.
                self.bypass_count += 1
                log.debug("split-tunnel bypass %s (%s)", host, decision.reason)
                remote_r, remote_w = await asyncio.open_connection(host, port)
            else:
                remote_r, remote_w = await self._dial(host, port)
            # success reply
            writer.write(b"\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00")
            await writer.drain()

            await self._pipe(reader, writer, remote_r, remote_w)
        except DirectDialRefused as exc:
            self.refused_connects += 1
            log.warning("refused CONNECT (fail-closed): %s peer=%s", exc, peer)
            try:
                # SOCKS5 general failure
                writer.write(b"\x05\x01\x00\x01" + b"\x00" * 6)
                await writer.drain()
            except Exception:  # noqa: BLE001
                pass
        except asyncio.IncompleteReadError:
            pass
        except Exception as exc:  # noqa: BLE001
            log.debug("client %s error: %s", peer, exc)
            try:
                writer.write(b"\x05\x01\x00\x01" + b"\x00" * 6)
                await writer.drain()
            except Exception:  # noqa: BLE001
                pass
        finally:
            self.active = max(0, self.active - 1)
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:  # noqa: BLE001
                pass

    async def _dial(
        self, host: str, port: int
    ) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        if not self.proxy_chain:
            if self.refuse_direct:
                raise DirectDialRefused(
                    "no live hops — fail-closed refuses direct clearnet dial"
                )
            return await asyncio.open_connection(host, port)

        try:
            from python_socks.async_.asyncio import Proxy
        except ImportError as exc:
            raise RuntimeError("python-socks is required for chaining") from exc

        # Nested chain: outermost first
        proxy_objs = []
        for url in self.proxy_chain:
            proxy_objs.append(Proxy.from_url(url))

        # python-socks supports chain via Proxy.chain
        if len(proxy_objs) == 1:
            sock = await proxy_objs[0].connect(dest_host=host, dest_port=port)
        else:
            try:
                chain = Proxy.chain(*proxy_objs)  # type: ignore[attr-defined]
                sock = await chain.connect(dest_host=host, dest_port=port)
            except Exception:
                if not self.allow_partial_chain:
                    log.error(
                        "full multi-hop chain failed; refuse_direct partial fallback disabled"
                    )
                    raise DirectDialRefused(
                        "multi-hop chain failed and allow_partial_chain is false"
                    ) from None
                # Explicit opt-in: connect through first hop only
                log.warning("full chain failed; allow_partial_chain — first hop only")
                sock = await proxy_objs[0].connect(dest_host=host, dest_port=port)

        return await asyncio.open_connection(sock=sock)

    async def _pipe(
        self,
        c_reader: asyncio.StreamReader,
        c_writer: asyncio.StreamWriter,
        r_reader: asyncio.StreamReader,
        r_writer: asyncio.StreamWriter,
    ) -> None:
        async def pump(src: asyncio.StreamReader, dst: asyncio.StreamWriter, inbound: bool) -> None:
            try:
                while True:
                    data = await src.read(65536)
                    if not data:
                        break
                    if inbound:
                        self.bytes_in += len(data)
                    else:
                        self.bytes_out += len(data)
                    dst.write(data)
                    await dst.drain()
            except Exception:  # noqa: BLE001
                pass
            finally:
                try:
                    dst.close()
                except Exception:  # noqa: BLE001
                    pass

        await asyncio.gather(
            pump(c_reader, r_writer, inbound=False),
            pump(r_reader, c_writer, inbound=True),
        )
