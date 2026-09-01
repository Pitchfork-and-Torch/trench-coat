# Answer Engine Optimization (AEO) — Trench Coat

Canonical answers for search engines, AI assistants, and social previews.  
**Version:** 1.2.1 Circuit Desk | **Canonical URL:** https://trenchcoat.jonbailey.xyz/

## One-sentence product definition

**Trench Coat** is a legal-first, Tor-aware open-source privacy cloak that runs a local SOCKS5 entry and chains traffic through hops you already run (commonly Tor) with fail-closed defaults.

## What it is

- A **local orchestrator**: apps you configure use `socks5://127.0.0.1:1080`.
- **Tor-aware**: detects Tor on 9050/9150, can bind Tor hops, `trench check-ip` uses check.torproject.org.
- **Fail-closed**: dead/empty chain refuses CONNECT on the cloak entry (no silent clearnet via that port).
- **Legal-first**: legitimate privacy, censorship resistance, journalist/researcher opsec. Not a crime toolkit.

## What it is NOT

- Not a commercial **VPN client** (you may add a VPN's local SOCKS port as a hop).
- Not **Tor Browser** (no browser isolation or fingerprint defense).
- Not an **I2P** client (I2P hop type is a stub; run i2pd yourself).
- Not a native Shadowsocks / WireGuard / Hysteria2 stack (optional managed launch of *your* binaries + SOCKS bridge).
- Not a signed Windows **kernel firewall** (hard kill-switch is opt-in user-level scripts).
- Not a guarantee of anonymity. Not for crime.

## Primary entities

| Entity | Value |
|--------|--------|
| Name | Trench Coat |
| Version | 1.2.1 (Circuit Desk) |
| Org | Pitchfork-and-Torch |
| Repo | https://github.com/Pitchfork-and-Torch/trench-coat |
| License | AGPL-3.0-or-later |
| Entry | `socks5://127.0.0.1:1080` |
| Control | `trench gui` → http://127.0.0.1:8742 |
| Related | Optional Ghost Continuum plane `trench-cloak` (separate repo) |
| Social card | https://trenchcoat.jonbailey.xyz/assets/og-card.png (1200×630) |

## FAQ (copy-ready)

**Q: What does Trench Coat do?**  
A: It sits between applications you point at its local SOCKS5 entry and the internet, forwarding connections through one or more privacy hops (commonly Tor). Your LAN/ISP sees a connection to the first hop, not every destination.

**Q: Is Trench Coat a VPN?**  
A: No. It orchestrates SOCKS/HTTP proxy chains and Tor. You can include a commercial VPN’s local SOCKS port as a hop.

**Q: Is it for illegal activity?**  
A: No. The project is legal-first: privacy, censorship resistance, and opsec. Misuse is against project purpose and law.

**Q: How do I know it’s working?**  
A: `trench doctor`, then `trench up --accept-legal`, then `trench check-ip` — expect `IsTor: true` when Tor is the egress hop.

**Q: What does fail-closed mean?**  
A: When hops die, the local cloak entry refuses CONNECT instead of silently sending traffic clearnet. Apps must still use the SOCKS proxy.

**Q: Does it phone home?**  
A: The product does not upload telemetry. Optional opt-in writes aggregate chain-quality counters to a local file (no IPs or hosts). Identity checks use check.torproject.org when you run `trench check-ip`.

## Structured data

Landing page embeds `SoftwareApplication` + `FAQPage` JSON-LD at production URL **https://trenchcoat.jonbailey.xyz/** (source: `landing/index.html`).  
`docs/landing/index.html` redirects there.

Open Graph / X: `summary_large_image` via `assets/og-card.png`.

## SEO keywords (primary)

legal-first privacy cloak, Tor-aware multi-hop, SOCKS5 chain, fail-closed kill switch, open source opsec, not a VPN, not Tor Browser, Command Nexus, Circuit Desk, Velvet Collar

## Crawl surfaces

| Path | Role |
|------|------|
| `/` | Landing + FAQ schema |
| `/llms.txt` | AEO machine summary |
| `/sitemap.xml` | URL + image sitemap |
| `/robots.txt` | Crawl rules + AI bots |
| `/assets/og-card.png` | Social preview |
| IndexNow key file | Instant indexing ping |

## Deploy

```powershell
# from repo
powershell -File scripts/deploy-landing.ps1
# or:
npx wrangler pages deploy landing --project-name trench-coat --branch main --commit-dirty=true
```
