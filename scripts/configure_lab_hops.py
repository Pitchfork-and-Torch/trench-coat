"""Configure Ghost/Journalist hops to local lab SOCKS ports and save config."""

from __future__ import annotations

from trenchcoat.config.loader import load_config, save_config
from trenchcoat.config.models import HopType


def set_hop(cfg, chain_name: str, hop_id: str, **kwargs) -> None:
    chain = cfg.get_chain(chain_name)
    if not chain:
        return
    for h in chain.hops:
        if h.id == hop_id:
            for k, v in kwargs.items():
                setattr(h, k, v)
            return


def main() -> None:
    cfg = load_config()

    set_hop(
        cfg,
        "ghost",
        "vpn-entry",
        type=HopType.SOCKS5,
        host="127.0.0.1",
        port=1088,
        label="VPN lab SOCKS (local hop - replace with real VPN SOCKS)",
        options={
            "role": "vpn-front",
            "lab": True,
            "provider_hint": "mullvad|proton|self-hosted",
        },
    )
    set_hop(
        cfg,
        "journalist",
        "relay-self",
        type=HopType.SELF_HOSTED,
        host="127.0.0.1",
        port=1081,
        label="Self-hosted lab relay (local hop - replace with VPS SOCKS)",
        options={"role": "entry-relay", "lab": True},
    )
    set_hop(
        cfg,
        "journalist",
        "vpn-mid",
        type=HopType.SOCKS5,
        host="127.0.0.1",
        port=1088,
        label="Mid VPN lab SOCKS (local hop - replace with real VPN)",
        options={"role": "vpn-mid", "lab": True},
    )
    for cname, hid in (
        ("ghost", "tor-exit"),
        ("journalist", "tor-final"),
        ("casual-shadow", "tor-local"),
    ):
        set_hop(cfg, cname, hid, host="127.0.0.1", port=9050)

    cfg.active_chain = "ghost"
    path = save_config(cfg)
    print("saved", path)
    print("active", cfg.active_chain)
    for name in ("ghost", "journalist"):
        ch = cfg.get_chain(name)
        assert ch
        hops = " | ".join(f"{h.id}={h.host}:{h.port}" for h in ch.hops)
        print(f"{name}: {hops}")


if __name__ == "__main__":
    main()
