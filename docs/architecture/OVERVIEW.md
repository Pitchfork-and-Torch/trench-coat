# Architecture Overview — Trench Coat

## Design principles

1. **CLI is the source of truth** — GUI is a control surface.  
2. **Fail closed** — broken chain → no silent direct traffic.  
3. **Pluggable hops** — every protocol is a driver behind one interface.  
4. **Local-first** — dossiers and configs stay on-metal unless user exports.  
5. **Legal-first** — no modules whose primary purpose is abuse.

## Components

### Config (`trenchcoat.config`)

Pydantic models for hops, chains, policies, split-tunnel rules. YAML on disk via `platformdirs`. Presets mint opinionated starting chains.

### Hops (`trenchcoat.hops`)

`Hop` ABC with `probe()` and `as_proxy_url()`. Implementations:

| Type | MVP | Notes |
|------|-----|-------|
| socks5 / residential / self_hosted | Live | SOCKS5 handshake + CONNECT probe |
| http / https | Live | HTTP CONNECT probe |
| tor | Live | SOCKS5 + bootstrap messaging |
| wireguard / shadowsocks / hysteria2 / i2p | Stub | Use `options.socks_bridge` until native drivers |

### Engine (`trenchcoat.engine`)

- **ChainBuilder** — instantiate hops, probe, optional mid-hop shuffle, expose proxy URL list  
- **ChainRotator** — rebuild on interval  
- **ChainProxyServer** — local SOCKS5; dials destinations via `python-socks` nested proxies  
- **KillSwitch** — soft always; hard OS rules phased  
- **DnsGuard** — recommendations + crude IPv6 detection  
- **CloakEngine** — orchestration + status DTO for API/CLI  

### Control plane (`trenchcoat.api`)

FastAPI: `/api/status`, `/api/presets`, `/ws/status`. Serves GUI dist when present.

### Presentation

- **CLI** — Rich + Click, noir narration  
- **gui/web** — canvas city map, hop health, metrics  
- **gui/tauri** — shell for packaging (Phase 4)

## System-wide routing (Phase 2+)

| OS | Mechanism |
|----|-----------|
| Linux | nftables / iptables TPROXY or policy routing into userspace |
| macOS | pf anchors + utun |
| Windows | WFP callout driver or WinDivert-class user strategy; strict code signing |

MVP deliberately uses **application SOCKS entry** so the project is usable without kernel drivers on day one.

## Trust boundaries

```text
[Untrusted net] ← hops → [Trench process] ← loopback SOCKS → [Apps]
                              ↑
                      [User config / GUI on localhost]
```

Never bind the control API to non-loopback without auth (future).

## Performance notes

- Nested SOCKS multiplies latency; profiles document the trade.  
- Health probes should not storm exit policies; interval defaults are conservative.  
- Future Rust data-plane can replace `ChainProxyServer` while keeping Python control plane.
