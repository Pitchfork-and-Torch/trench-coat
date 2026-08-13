# System routing — Phase 2 Circuit City

## Goals

1. Prefer **app-level SOCKS** (`socks5://127.0.0.1:1080`) — safest default  
2. Offer **soft system proxy** (WinHTTP / OS settings) for broader coverage  
3. Document **hard transparent** paths (nftables, pf, WFP) without auto-bricking machines  

## Soft path

```bash
trench route soft      # best-effort system proxy toward cloak
trench route revert
```

Browsers often use WinINET on Windows — set SOCKS in the browser or use the companion extension.

## Split tunnel

Rules live on each chain (`split_tunnel` in config). Evaluated at SOCKS CONNECT time:

- `exclude` + CIDR/domain → direct dial  
- default → through multi-hop chain  

```bash
trench split
```

## DNS

```bash
trench doh example.com --via-cloak
```

DoH JSON queries ride the egress hop when available.

## IPv6

```bash
trench ipv6 status
trench ipv6 disable --force   # Linux only best-effort; Windows/macOS: guided commands
```

## Hard path scripts

```bash
trench route scripts --out packaging
```

Emits `nft-trenchcoat.nft`, `pf-trenchcoat.conf`, `windows-wfp-notes.md`.  
**Never load hard rules without a tested undo path.**
