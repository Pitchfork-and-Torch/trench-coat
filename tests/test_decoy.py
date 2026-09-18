import pytest

from trenchcoat.engine.decoy import DecoyGenerator


@pytest.mark.asyncio
async def test_decoy_pulse_direct_may_fail_offline():
    g = DecoyGenerator(proxy_urls=[], interval_seconds=60)
    await g.pulse()
    # either success or error counted
    assert g.stats.sent + g.stats.errors >= 1
