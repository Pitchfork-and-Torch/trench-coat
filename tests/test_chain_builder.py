import pytest

from trenchcoat.config.models import ChainConfig, ChainPolicy, HopConfig, HopType, ProfileName
from trenchcoat.engine.chain import ChainBuilder
from trenchcoat.hops.base import HopHealth


@pytest.mark.asyncio
async def test_build_with_dead_hops_fail_closed_message():
    chain = ChainConfig(
        name="test",
        profile=ProfileName.CUSTOM,
        hops=[
            HopConfig(
                id="dead-socks",
                type=HopType.SOCKS5,
                host="127.0.0.1",
                port=1,  # almost certainly closed
            )
        ],
        policy=ChainPolicy(min_hops=1, fail_closed=True),
    )
    builder = ChainBuilder(chain)
    snap = await builder.build()
    assert snap.hops[0].health == HopHealth.DEAD
    assert snap.healthy is False
    assert builder.proxy_urls() == []


@pytest.mark.asyncio
async def test_stub_hop_unknown():
    chain = ChainConfig(
        name="stub",
        profile=ProfileName.CUSTOM,
        hops=[
            HopConfig(id="wg", type=HopType.WIREGUARD, host="127.0.0.1", port=51820),
        ],
        policy=ChainPolicy(min_hops=1),
    )
    snap = await ChainBuilder(chain).build()
    assert snap.hops[0].health == HopHealth.UNKNOWN
