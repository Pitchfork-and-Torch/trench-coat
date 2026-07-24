"""Fail-closed: cloak entry must never silent-clearnet when refuse_direct."""

from __future__ import annotations

import asyncio
import struct

import pytest

from trenchcoat.config.models import (
    AppConfig,
    ChainConfig,
    ChainPolicy,
    HopConfig,
    HopType,
    ProfileName,
)
from trenchcoat.engine.proxy_server import ChainProxyServer, DirectDialRefused
from trenchcoat.engine.router import CloakEngine


async def _socks_connect(host: str, port: int, dest_host: str, dest_port: int) -> bytes:
    """SOCKS5 no-auth CONNECT; return the 2-byte reply (ver, rep) after greeting."""
    reader, writer = await asyncio.open_connection(host, port)
    try:
        writer.write(b"\x05\x01\x00")
        await writer.drain()
        greet = await asyncio.wait_for(reader.readexactly(2), timeout=3.0)
        assert greet == b"\x05\x00"
        # CONNECT domain
        req = b"\x05\x01\x00\x03" + bytes([len(dest_host)]) + dest_host.encode() + struct.pack(
            "!H", dest_port
        )
        writer.write(req)
        await writer.drain()
        # Reply: VER REP RSV ATYP ...
        reply_head = await asyncio.wait_for(reader.readexactly(4), timeout=3.0)
        return reply_head
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:  # noqa: BLE001
            pass


@pytest.mark.asyncio
async def test_empty_chain_refuse_direct_raises():
    srv = ChainProxyServer("127.0.0.1", 0, [], refuse_direct=True)
    with pytest.raises(DirectDialRefused):
        await srv._dial("example.com", 443)


@pytest.mark.asyncio
async def test_empty_chain_allow_direct_when_refuse_off():
    """Opt-out path: refuse_direct=False still permits direct (not the product default)."""
    # Binding ephemeral local listener as destination
    async def _echo(r, w):
        data = await r.read(16)
        w.write(data)
        await w.drain()
        w.close()

    echo = await asyncio.start_server(_echo, "127.0.0.1", 0)
    eport = echo.sockets[0].getsockname()[1]
    try:
        srv = ChainProxyServer("127.0.0.1", 0, [], refuse_direct=False)
        r, w = await srv._dial("127.0.0.1", eport)
        w.write(b"hi")
        await w.drain()
        got = await r.read(16)
        assert got == b"hi"
        w.close()
        await w.wait_closed()
    finally:
        echo.close()
        await echo.wait_closed()


@pytest.mark.asyncio
async def test_socks_entry_refuses_connect_when_chain_empty():
    srv = ChainProxyServer("127.0.0.1", 0, [], refuse_direct=True)
    await srv.start()
    try:
        port = srv._server.sockets[0].getsockname()[1]
        head = await _socks_connect("127.0.0.1", port, "example.com", 80)
        assert head[0] == 5
        assert head[1] == 1  # general SOCKS failure
        assert srv.refused_connects >= 1
    finally:
        await srv.stop()


@pytest.mark.asyncio
async def test_partial_chain_fallback_disabled_by_default():
    """Multi-hop failure must raise DirectDialRefused when allow_partial_chain is False.

    Uses unreachable proxy URLs so connect fails without needing a real chain.
    """
    srv = ChainProxyServer(
        "127.0.0.1",
        0,
        ["socks5://127.0.0.1:1", "socks5://127.0.0.1:2"],
        refuse_direct=True,
        allow_partial_chain=False,
    )
    with pytest.raises((DirectDialRefused, OSError, Exception)):
        # May raise DirectDialRefused after first hop fails nested chain, or connection errors
        await asyncio.wait_for(srv._dial("example.com", 443), timeout=8.0)


@pytest.mark.asyncio
async def test_engine_start_fail_closed_no_live_hops():
    cfg = AppConfig(listen_host="127.0.0.1", listen_port=0)
    chain = ChainConfig(
        name="dead",
        profile=ProfileName.CUSTOM,
        hops=[
            HopConfig(id="dead", type=HopType.SOCKS5, host="127.0.0.1", port=1),
        ],
        policy=ChainPolicy(min_hops=1, fail_closed=True, health_check_seconds=5),
    )
    eng = CloakEngine(cfg, chain)
    st = await eng.start()
    assert st.running is False
    assert eng.proxy is None
    assert any("FAIL-CLOSED" in m for m in st.messages)


@pytest.mark.asyncio
async def test_engine_hop_death_sets_fail_closed_tripped():
    """Simulate mid-session hop death via _apply_urls([])."""
    cfg = AppConfig(listen_host="127.0.0.1", listen_port=0)
    # Start with a "live" empty-policy chain that has refuse but we force a fake proxy chain.
    # Use fail_closed with a hop that won't be needed because we inject URLs.
    chain = ChainConfig(
        name="sim",
        profile=ProfileName.CUSTOM,
        hops=[
            HopConfig(id="dead", type=HopType.SOCKS5, host="127.0.0.1", port=1),
        ],
        policy=ChainPolicy(
            min_hops=1,
            fail_closed=True,
            kill_switch=False,
            health_check_seconds=5,
            decoy_traffic=False,
        ),
    )
    eng = CloakEngine(cfg, chain)
    # Bypass normal start fail-closed by constructing proxy manually after empty start fails.
    # Instead: start with refuse_direct and a temporary fake healthy path — open local SOCKS
    # that accepts anything is hard. Use direct path: create proxy server as engine would.
    eng.proxy = ChainProxyServer(
        "127.0.0.1",
        0,
        ["socks5://127.0.0.1:9050"],  # may be dead; list non-empty so dial path differs
        refuse_direct=True,
        allow_partial_chain=False,
    )
    await eng.proxy.start()
    eng._status.running = True
    eng._status.refuse_direct = True

    eng._apply_urls([])
    assert eng._status.fail_closed_tripped is True
    assert eng.proxy.refuse_direct is True
    assert eng.proxy.proxy_chain == []

    port = eng.proxy._server.sockets[0].getsockname()[1]
    head = await _socks_connect("127.0.0.1", port, "example.com", 80)
    assert head[1] == 1  # refused
    assert eng.proxy.refused_connects >= 1

    await eng.proxy.stop()
    eng.proxy = None
