"""Hop probe honesty: CONNECT-refused is DEGRADED, not HEALTHY or DEAD."""

from __future__ import annotations

import asyncio

import pytest

from trenchcoat.config.models import HopConfig, HopType
from trenchcoat.hops.base import HopHealth
from trenchcoat.hops.http_proxy import HttpProxyHop
from trenchcoat.hops.socks5 import Socks5Hop


async def _socks_handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter, *, ok: bool) -> None:
    try:
        head = await reader.readexactly(2)
        nmethods = head[1]
        if nmethods:
            await reader.readexactly(nmethods)
        writer.write(b"\x05\x00")
        await writer.drain()
        req = await reader.readexactly(4)
        atyp = req[3]
        if atyp == 3:
            ln = (await reader.readexactly(1))[0]
            await reader.readexactly(ln + 2)
        elif atyp == 1:
            await reader.readexactly(6)
        elif atyp == 4:
            await reader.readexactly(18)
        if ok:
            writer.write(b"\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00")
        else:
            writer.write(b"\x05\x01\x00\x01\x00\x00\x00\x00\x00\x00")
        await writer.drain()
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:  # noqa: BLE001
            pass


@pytest.mark.asyncio
async def test_socks_connect_ok_is_healthy():
    server = await asyncio.start_server(
        lambda r, w: _socks_handler(r, w, ok=True), "127.0.0.1", 0
    )
    port = server.sockets[0].getsockname()[1]
    try:
        hop = Socks5Hop(HopConfig(id="s", type=HopType.SOCKS5, host="127.0.0.1", port=port))
        st = await hop.probe(timeout=3.0)
        assert st.health == HopHealth.HEALTHY
        assert st.error is None
    finally:
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_socks_connect_refused_is_degraded_not_healthy():
    server = await asyncio.start_server(
        lambda r, w: _socks_handler(r, w, ok=False), "127.0.0.1", 0
    )
    port = server.sockets[0].getsockname()[1]
    try:
        hop = Socks5Hop(HopConfig(id="s", type=HopType.SOCKS5, host="127.0.0.1", port=port))
        st = await hop.probe(timeout=3.0)
        assert st.health == HopHealth.DEGRADED
        assert st.error
        assert "refused" in st.error.lower()
    finally:
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_closed_port_is_dead():
    hop = Socks5Hop(HopConfig(id="s", type=HopType.SOCKS5, host="127.0.0.1", port=1))
    st = await hop.probe(timeout=1.5)
    assert st.health == HopHealth.DEAD


@pytest.mark.asyncio
async def test_http_connect_forbidden_is_degraded():
    async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            await reader.readuntil(b"\r\n\r\n")
            writer.write(b"HTTP/1.1 403 Forbidden\r\n\r\n")
            await writer.drain()
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:  # noqa: BLE001
                pass

    server = await asyncio.start_server(handler, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    try:
        hop = HttpProxyHop(HopConfig(id="h", type=HopType.HTTP, host="127.0.0.1", port=port))
        st = await hop.probe(timeout=3.0)
        assert st.health == HopHealth.DEGRADED
        assert st.error
    finally:
        server.close()
        await server.wait_closed()
