"""Configuration models for Trench Coat chains, hops, and runtime policy."""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class HopType(str, Enum):
    SOCKS5 = "socks5"
    HTTP = "http"
    HTTPS = "https"
    TOR = "tor"
    I2P = "i2p"
    SHADOWSOCKS = "shadowsocks"
    WIREGUARD = "wireguard"
    HYSTERIA2 = "hysteria2"
    RESIDENTIAL = "residential"
    SELF_HOSTED = "self_hosted"
    BRIDGE = "bridge"  # obfs4 / snowflake / meek


class ProfileName(str, Enum):
    GHOST = "ghost"
    JOURNALIST = "journalist"
    WHISTLEBLOWER = "whistleblower"
    CASUAL_SHADOW = "casual_shadow"
    PARANOID = "paranoid"
    CUSTOM = "custom"


class HopConfig(BaseModel):
    """A single hop in the trench coat chain."""

    id: str
    type: HopType
    host: str = "127.0.0.1"
    port: int = Field(ge=1, le=65535)
    username: str | None = None
    password: str | None = None
    # Provider-specific extras (WireGuard conf path, SS method, etc.)
    options: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    weight: float = 1.0
    label: str | None = None
    country: str | None = None

    @property
    def display_name(self) -> str:
        return self.label or f"{self.type.value}://{self.host}:{self.port}"

    def endpoint(self) -> str:
        return f"{self.host}:{self.port}"


class SplitTunnelRule(BaseModel):
    """Include or exclude traffic from the cloak."""

    pattern: str  # process name, CIDR, domain, or keyword
    action: Literal["include", "exclude"] = "exclude"
    reason: str = ""
    kind: Literal["auto", "cidr", "domain", "process"] = "auto"


class ChainPolicy(BaseModel):
    """Runtime policy for a chain."""

    min_hops: int = Field(default=2, ge=1, le=32)
    max_hops: int = Field(default=10, ge=1, le=32)
    rotation_minutes: int = Field(default=15, ge=0)  # 0 = no rotation
    health_check_seconds: int = Field(default=30, ge=5)
    kill_switch: bool = True
    strict_kill_switch: bool = True  # drop ALL non-chain traffic when active
    block_ipv6: bool = True
    dns_leak_protection: bool = True
    webrtc_block_hint: bool = True  # browser guidance + system DNS lockdown
    randomize_order: bool = False
    decoy_traffic: bool = False
    decoy_interval_seconds: int = 60
    fail_closed: bool = True
    # When False (default), multi-hop dial failure does not silently degrade to first hop only.
    allow_partial_chain: bool = False


class ChainConfig(BaseModel):
    """A named multi-hop cloak configuration."""

    name: str
    profile: ProfileName = ProfileName.CUSTOM
    description: str = ""
    hops: list[HopConfig] = Field(default_factory=list)
    policy: ChainPolicy = Field(default_factory=ChainPolicy)
    split_tunnel: list[SplitTunnelRule] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

    @field_validator("hops")
    @classmethod
    def validate_hops_unique_ids(cls, hops: list[HopConfig]) -> list[HopConfig]:
        ids = [h.id for h in hops]
        if len(ids) != len(set(ids)):
            raise ValueError("Hop IDs must be unique within a chain")
        return hops

    def active_hops(self) -> list[HopConfig]:
        return [h for h in self.hops if h.enabled]


class AppConfig(BaseModel):
    """Top-level application configuration."""

    version: int = 1
    active_chain: str | None = None
    chains: list[ChainConfig] = Field(default_factory=list)
    listen_host: str = "127.0.0.1"
    listen_port: int = 1080
    control_port: int = 8742
    noir_mode: bool = True
    log_level: str = "INFO"
    encrypt_logs: bool = True
    auto_start: bool = False
    community_sharing: bool = False  # opt-in only
    telemetry_opt_in: bool = False  # Phase 5 — anonymous local quality stats
    accepted_legal_notice: bool = False

    def get_chain(self, name: str | None = None) -> ChainConfig | None:
        target = name or self.active_chain
        if not target:
            return None
        for chain in self.chains:
            if chain.name == target:
                return chain
        return None
