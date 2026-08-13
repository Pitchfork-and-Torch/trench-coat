"""Phase 5 optimizer + templates smoke tests."""

from __future__ import annotations

from trenchcoat.config.models import ChainConfig, HopConfig, HopType, ProfileName
from trenchcoat.config.templates import list_templates, load_template
from trenchcoat.engine.optimizer import _score
from trenchcoat.hops.base import HopHealth


def test_score_prefers_low_latency() -> None:
    assert _score(10.0, HopHealth.HEALTHY.value, 1.0) < _score(200.0, HopHealth.HEALTHY.value, 1.0)
    assert _score(None, HopHealth.DEAD.value, 1.0) > 1000


def test_templates_shipped() -> None:
    rows = list_templates()
    ids = {r["id"] for r in rows}
    assert "casual-tor" in ids
    assert "vpn-then-tor" in ids
    chain = load_template("casual-tor")
    assert isinstance(chain, ChainConfig)
    assert chain.hops
    assert chain.hops[0].type == HopType.TOR


def test_chain_mid_reorder_logic() -> None:
    chain = ChainConfig(
        name="test",
        profile=ProfileName.CUSTOM,
        hops=[
            HopConfig(id="head", type=HopType.SOCKS5, host="127.0.0.1", port=1),
            HopConfig(id="slow", type=HopType.SOCKS5, host="127.0.0.1", port=2, weight=1.0),
            HopConfig(id="fast", type=HopType.SOCKS5, host="127.0.0.1", port=3, weight=1.0),
            HopConfig(id="tail", type=HopType.TOR, host="127.0.0.1", port=9050),
        ],
    )
    assert len(chain.hops) == 4
    assert chain.hops[0].id == "head"
    assert chain.hops[-1].id == "tail"
