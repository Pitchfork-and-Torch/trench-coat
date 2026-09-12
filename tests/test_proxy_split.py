import asyncio

import pytest

from trenchcoat.config.models import SplitTunnelRule
from trenchcoat.engine.proxy_server import ChainProxyServer
from trenchcoat.engine.split_tunnel import SplitTunnelEngine


@pytest.mark.asyncio
async def test_proxy_starts_and_stops():
    eng = SplitTunnelEngine(
        [SplitTunnelRule(pattern="127.0.0.0/8", action="exclude", reason="loop")]
    )
    srv = ChainProxyServer("127.0.0.1", 0, [], split_tunnel=eng)
    # bind ephemeral
    await srv.start()
    assert srv._server is not None
    socks = srv._server.sockets
    assert socks
    port = socks[0].getsockname()[1]
    # SOCKS5 no-auth greeting only
    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    writer.write(b"\x05\x01\x00")
    await writer.drain()
    resp = await reader.readexactly(2)
    assert resp == b"\x05\x00"
    writer.close()
    await writer.wait_closed()
    await srv.stop()
