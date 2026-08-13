"""SOCKS5 hop probe and chain helper."""

from __future__ import annotations

import asyncio
import socket
import struct
import time

from trenchcoat.hops.base import Hop, HopHealth, HopStatus


class Socks5Hop(Hop):
    async def probe(self, timeout: float = 5.0) -> HopStatus:
        start = time.perf_counter()
        try:
            await asyncio.wait_for(self._handshake(), timeout=timeout)
            latency = (time.perf_counter() - start) * 1000
            self.status = HopStatus(
                hop_id=self.config.id,
                health=HopHealth.HEALTHY if latency < 2000 else HopHealth.DEGRADED,
                latency_ms=round(latency, 2),
                last_check=time.time(),
            )
        except Exception as exc:  # noqa: BLE001 — surface any probe failure
            self.status = HopStatus(
                hop_id=self.config.id,
                health=HopHealth.DEAD,
                last_check=time.time(),
                error=str(exc),
            )
        return self.status

    async def _handshake(self) -> None:
        host, port = self.config.host, self.config.port
        reader, writer = await asyncio.open_connection(host, port)
        try:
            # greeting: VER=5, NMETHODS=1, METHOD=0 (no auth) or 2 (user/pass)
            if self.config.username:
                writer.write(b"\x05\x01\x02")
            else:
                writer.write(b"\x05\x01\x00")
            await writer.drain()
            resp = await reader.readexactly(2)
            if resp[0] != 5:
                raise ConnectionError(f"Not SOCKS5 (ver={resp[0]})")
            method = resp[1]
            if method == 0xFF:
                raise ConnectionError("SOCKS5: no acceptable auth method")
            if method == 2:
                user = (self.config.username or "").encode()
                pw = (self.config.password or "").encode()
                auth = bytes([0x01, len(user)]) + user + bytes([len(pw)]) + pw
                writer.write(auth)
                await writer.drain()
                auth_resp = await reader.readexactly(2)
                if auth_resp[1] != 0:
                    raise ConnectionError("SOCKS5 authentication failed")
            # CONNECT to a well-known check host via this hop (does not complete full HTTP)
            # We only verify the proxy accepts CONNECT to example.com:80
            dest = b"example.com"
            req = b"\x05\x01\x00\x03" + bytes([len(dest)]) + dest + struct.pack("!H", 80)
            writer.write(req)
            await writer.drain()
            # Read at least reply header (variable bound addr)
            hdr = await reader.readexactly(4)
            if hdr[1] != 0:
                # Some proxies reject example.com; still counts as "alive" if we got SOCKS reply
                if hdr[0] == 5:
                    return
                raise ConnectionError(f"SOCKS5 connect failed: rep={hdr[1]}")
            atyp = hdr[3]
            if atyp == 1:
                await reader.readexactly(4 + 2)
            elif atyp == 3:
                ln = (await reader.readexactly(1))[0]
                await reader.readexactly(ln + 2)
            elif atyp == 4:
                await reader.readexactly(16 + 2)
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:  # noqa: BLE001
                pass


def resolve_socks_addr(host: str, port: int) -> tuple[str, int]:
    """Normalize host for connection (IPv6-safe later)."""
    try:
        socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ConnectionError(f"Cannot resolve {host}: {exc}") from exc
    return host, port
