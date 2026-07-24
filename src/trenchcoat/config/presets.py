"""Built-in cloak profiles — Ghost, Journalist, Whistleblower, Casual Shadow, Paranoid."""

from __future__ import annotations

from trenchcoat.config.models import (
    ChainConfig,
    ChainPolicy,
    HopConfig,
    HopType,
    ProfileName,
    SplitTunnelRule,
)


def _tor_hop(hop_id: str = "tor-local", port: int = 9050) -> HopConfig:
    return HopConfig(
        id=hop_id,
        type=HopType.TOR,
        host="127.0.0.1",
        port=port,
        label="Tor (local SOCKS)",
        country="??",
    )


def preset_casual_shadow() -> ChainConfig:
    """Light privacy: single Tor hop. Everyday browsing, low friction."""
    return ChainConfig(
        name="casual-shadow",
        profile=ProfileName.CASUAL_SHADOW,
        description="One layer of night. Tor only. Fast enough for the rain.",
        hops=[_tor_hop()],
        policy=ChainPolicy(
            min_hops=1,
            max_hops=3,
            rotation_minutes=0,
            kill_switch=True,
            strict_kill_switch=False,
            randomize_order=False,
            decoy_traffic=False,
        ),
        split_tunnel=[
            SplitTunnelRule(pattern="192.168.0.0/16", action="exclude", reason="LAN"),
            SplitTunnelRule(pattern="10.0.0.0/8", action="exclude", reason="LAN"),
            SplitTunnelRule(pattern="127.0.0.0/8", action="exclude", reason="loopback"),
        ],
        tags=["starter", "tor", "low-latency"],
    )


def preset_ghost() -> ChainConfig:
    """Balanced cloak: commercial VPN hop + Tor. Solid daily opsec."""
    return ChainConfig(
        name="ghost",
        profile=ProfileName.GHOST,
        description="VPN front door, Tor back alley. The classic ghost walk.",
        hops=[
            HopConfig(
                id="vpn-entry",
                type=HopType.SOCKS5,
                host="127.0.0.1",
                port=1088,
                label="Local VPN SOCKS (configure me)",
                options={"provider_hint": "mullvad|proton|self-hosted"},
            ),
            _tor_hop("tor-exit"),
        ],
        policy=ChainPolicy(
            min_hops=2,
            max_hops=5,
            rotation_minutes=30,
            kill_switch=True,
            strict_kill_switch=True,
            block_ipv6=True,
            dns_leak_protection=True,
        ),
        split_tunnel=[
            SplitTunnelRule(pattern="192.168.0.0/16", action="exclude", reason="LAN"),
            SplitTunnelRule(pattern="banking", action="exclude", reason="optional banking exclusion"),
        ],
        tags=["recommended", "vpn", "tor"],
    )


def preset_journalist() -> ChainConfig:
    """Field correspondent profile: resilient multi-hop, obfuscation-ready."""
    return ChainConfig(
        name="journalist",
        profile=ProfileName.JOURNALIST,
        description=(
            "For those who write the truth under hostile skies. "
            "Self-hosted relay → obfuscated path → Tor. Fail closed."
        ),
        hops=[
            HopConfig(
                id="relay-self",
                type=HopType.SELF_HOSTED,
                host="127.0.0.1",
                port=1081,
                label="Self-hosted relay (configure me)",
                options={"obfs": "obfs4|snowflake|meek"},
            ),
            HopConfig(
                id="vpn-mid",
                type=HopType.SOCKS5,
                host="127.0.0.1",
                port=1088,
                label="Jurisdiction-diverse VPN",
            ),
            _tor_hop("tor-final"),
        ],
        policy=ChainPolicy(
            min_hops=3,
            max_hops=7,
            rotation_minutes=20,
            health_check_seconds=20,
            kill_switch=True,
            strict_kill_switch=True,
            block_ipv6=True,
            dns_leak_protection=True,
            decoy_traffic=True,
            decoy_interval_seconds=90,
            fail_closed=True,
        ),
        tags=["field", "obfs", "fail-closed"],
    )


def preset_whistleblower() -> ChainConfig:
    """Maximum practical anonymity short of air-gap."""
    return ChainConfig(
        name="whistleblower",
        profile=ProfileName.WHISTLEBLOWER,
        description=(
            "Deep cover. Residential or trusted entry → multi-jurisdiction hops → "
            "Tor. Rotation aggressive. Deniable config storage recommended."
        ),
        hops=[
            HopConfig(
                id="residential-entry",
                type=HopType.RESIDENTIAL,
                host="127.0.0.1",
                port=1090,
                label="Trusted residential / CDN front (configure me)",
            ),
            HopConfig(
                id="vps-a",
                type=HopType.SELF_HOSTED,
                host="127.0.0.1",
                port=1082,
                label="VPS hop A (configure me)",
            ),
            HopConfig(
                id="vps-b",
                type=HopType.SOCKS5,
                host="127.0.0.1",
                port=1083,
                label="VPS hop B (configure me)",
            ),
            _tor_hop("tor-final"),
        ],
        policy=ChainPolicy(
            min_hops=4,
            max_hops=10,
            rotation_minutes=12,
            health_check_seconds=15,
            kill_switch=True,
            strict_kill_switch=True,
            block_ipv6=True,
            dns_leak_protection=True,
            randomize_order=True,
            decoy_traffic=True,
            decoy_interval_seconds=45,
            fail_closed=True,
        ),
        tags=["high-risk", "max-hops", "rotation"],
    )


def preset_paranoid() -> ChainConfig:
    """Everything on. Latency be damned. The shadows swallow the clock."""
    return ChainConfig(
        name="paranoid",
        profile=ProfileName.PARANOID,
        description=(
            "Full cloak. Randomized order (where safe), decoy traffic, "
            "strict kill-switch, frequent rebuilds. Expect slowness. Expect silence."
        ),
        hops=[
            HopConfig(
                id="entry-obfs",
                type=HopType.HYSTERIA2,
                host="127.0.0.1",
                port=443,
                label="Hysteria2 / QUIC camouflage (configure me)",
                options={"camouflage": True},
            ),
            HopConfig(
                id="mid-ss",
                type=HopType.SHADOWSOCKS,
                host="127.0.0.1",
                port=8388,
                label="Shadowsocks mid-hop (configure me)",
            ),
            HopConfig(
                id="mid-vpn",
                type=HopType.WIREGUARD,
                host="127.0.0.1",
                port=51820,
                label="WireGuard tunnel (configure me)",
                options={"conf": ""},
            ),
            HopConfig(
                id="i2p-optional",
                type=HopType.I2P,
                host="127.0.0.1",
                port=4447,
                label="I2P HTTP proxy (optional)",
                enabled=False,
            ),
            _tor_hop("tor-final"),
        ],
        policy=ChainPolicy(
            min_hops=3,
            max_hops=12,
            rotation_minutes=8,
            health_check_seconds=12,
            kill_switch=True,
            strict_kill_switch=True,
            block_ipv6=True,
            dns_leak_protection=True,
            randomize_order=True,
            decoy_traffic=True,
            decoy_interval_seconds=30,
            fail_closed=True,
        ),
        tags=["paranoid", "slow", "max-security"],
    )


PRESETS: dict[str, ChainConfig] = {
    "casual-shadow": preset_casual_shadow(),
    "ghost": preset_ghost(),
    "journalist": preset_journalist(),
    "whistleblower": preset_whistleblower(),
    "paranoid": preset_paranoid(),
}


def list_presets() -> list[ChainConfig]:
    return list(PRESETS.values())


def get_preset(name: str) -> ChainConfig:
    key = name.lower().replace("_", "-")
    if key not in PRESETS:
        raise KeyError(f"Unknown profile '{name}'. Available: {', '.join(PRESETS)}")
    # Return a deep copy so callers can mutate safely
    return PRESETS[key].model_copy(deep=True)
