from trenchcoat.config.models import HopConfig, HopType
from trenchcoat.engine.tor_detect import TorEndpoint, bind_chain_to_tor, port_open


def test_port_open_closed():
    assert port_open("127.0.0.1", 1, timeout=0.2) is False


def test_bind_chain_to_tor():
    hops = [
        HopConfig(id="t", type=HopType.TOR, host="127.0.0.1", port=9050),
        HopConfig(id="s", type=HopType.SOCKS5, host="127.0.0.1", port=1088),
    ]
    ep = TorEndpoint(host="127.0.0.1", port=9150)
    n = bind_chain_to_tor(hops, ep)
    assert n == 1
    assert hops[0].port == 9150
    assert hops[1].port == 1088
