from trenchcoat.config.models import SplitTunnelRule
from trenchcoat.engine.split_tunnel import SplitTunnelEngine


def test_cidr_exclude():
    eng = SplitTunnelEngine(
        [SplitTunnelRule(pattern="192.168.0.0/16", action="exclude", reason="LAN")]
    )
    d = eng.decide("192.168.1.50")
    assert d.bypass is True
    assert eng.decide("8.8.8.8").bypass is False


def test_domain_suffix():
    eng = SplitTunnelEngine(
        [SplitTunnelRule(pattern="example.com", action="exclude", reason="test")]
    )
    assert eng.decide("www.example.com").bypass is True
    assert eng.decide("evil.com").bypass is False


def test_include_wins_order():
    eng = SplitTunnelEngine(
        [
            SplitTunnelRule(pattern="10.0.0.0/8", action="include", reason="force"),
            SplitTunnelRule(pattern="10.0.0.0/8", action="exclude", reason="lan"),
        ]
    )
    # first match wins
    assert eng.decide("10.1.2.3").bypass is False
