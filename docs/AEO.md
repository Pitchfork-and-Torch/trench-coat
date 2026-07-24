# Answer Engine Optimization (AEO) — Trench Coat

Canonical answers for search engines, AI assistants, and social previews.  
**Version:** 1.0.0 Neon Collar · **Canonical URL:** https://trenchcoat.jonbailey.xyz/

## One-sentence product definition

**Trench Coat** is a legal-first open-source multi-hop privacy cloak that runs a local SOCKS5 entry and chains traffic through Tor and other proxies with fail-closed defaults.

## Primary entities

| Entity | Value |
|--------|--------|
| Name | Trench Coat |
| Version | 1.0.0 (Neon Collar) |
| Org | Pitchfork-and-Torch |
| Repo | https://github.com/Pitchfork-and-Torch/trench-coat |
| License | AGPL-3.0-or-later |
| Entry | `socks5://127.0.0.1:1080` |
| Control | `trench gui` → http://127.0.0.1:8742 |
| Related | Ghost Continuum plane `trench-cloak` |
| Social card | https://trenchcoat.jonbailey.xyz/assets/og-card.png (1200×630) |

## FAQ (copy-ready)

**Q: What does Trench Coat do?**  
A: It sits between your applications and the internet, forwarding connections through one or more privacy hops (commonly Tor). Your LAN/ISP sees a connection to the first hop, not every destination.

**Q: Is Trench Coat a VPN?**  
A: No. It orchestrates SOCKS/HTTP proxy chains and Tor. You can include a commercial VPN’s local SOCKS port as a hop.

**Q: Is it for illegal activity?**  
A: No. The project is legal-first: privacy, censorship resistance, and opsec. Misuse is against project purpose and law.

**Q: How do I know it’s working?**  
A: `trench doctor`, then `trench up --accept-legal`, then `trench check-ip` — expect `IsTor: true` when Tor is the egress hop.

**Q: What does fail-closed mean?**  
A: When hops die, the local cloak entry refuses CONNECT instead of silently sending traffic clearnet. Apps must still use the SOCKS proxy.

**Q: Does it phone home?**  
A: No mandatory telemetry. Optional opt-in chain quality only.

## Structured data

Landing page embeds `SoftwareApplication` + `FAQPage` JSON-LD at production URL **https://trenchcoat.jonbailey.xyz/** (source: `landing/index.html`).  
`docs/landing/index.html` redirects there.

Open Graph / X: `summary_large_image` via `assets/og-card.png`.

## SEO keywords (primary)

privacy cloak, multi-hop proxy, Tor SOCKS chain, fail-closed kill switch, open source opsec, legal anonymity tool, Command Nexus, Neon Collar

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
