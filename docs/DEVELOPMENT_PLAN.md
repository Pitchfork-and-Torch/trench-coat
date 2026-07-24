# Development Plan — Trench Coat

## Phase 0 — Neon Thread ✅

- [x] Repo structure, AGPL, noir README & assets  
- [x] Config models + presets  
- [x] Hop probes (SOCKS5/HTTP/Tor)  
- [x] Local multi-hop SOCKS entry  
- [x] Kill-switch soft mode + doctor  
- [x] CLI + GUI + dossiers + CI  

## Phase 1 — Wet Pavement ✅

- [x] Concurrent hop probes  
- [x] Auto-detect Tor SOCKS + bind hops  
- [x] `check-ip` / API identity  
- [x] Default Casual Shadow  
- [x] start-tor scripts  
- [x] Tor control-port NEWNYM (`trench tor newnym`)  

## Phase 2 — Circuit City ✅

- [x] System routing docs + soft proxy + hard script emitters  
- [x] Split-tunnel engine (CIDR / domain / process) at SOCKS layer  
- [x] DoH via cloak (`trench doh`)  
- [x] IPv6 status / guided disable  

## Phase 3 — Obsidian Collar ✅

- [x] Shadowsocks / Hysteria2 / WireGuard managed hop drivers  
- [x] Bridge hop type (obfs4 / snowflake / meek via options)  
- [x] Plugin API v1 + example pad obfuscator  
- [x] Decoy traffic generator (rate-limited)  

## Phase 4 — Jazz for Ghosts ✅

- [x] Tauri config scaffold + packaging notes  
- [x] Noir Mode TTS (`trench speak`)  
- [x] City map depth/grid/trail upgrade  
- [x] Fingerprint companion extension (optional)  
- [x] PyInstaller spec  

## Phase 5 — Syndicate ✅

- [x] Opt-in anonymized chain quality telemetry (`trench telemetry`)  
- [x] Community chain templates (`configs/templates`, `trench templates`)  
- [x] Latency-aware optimizer (`trench optimize`)  
- [x] Third-party security audit readiness (`docs/security/THIRD_PARTY_AUDIT.md`)  
- [x] Production landing page + infographic (`landing/`, trenchcoat.jonbailey.xyz)  

## Phase 6 — Iron Collar (in progress)

- [x] Opt-in hard kill-switch with **undo-first** scripts (`trench killswitch hard`)  
- [x] Cross-platform hard script bundles (Windows netsh / Linux nft / macOS pf)  
- [x] Soft arm + disarm + `killswitch scripts` emitters  
- [x] Audit engagement + public findings response template (`docs/security/AUDIT_RESPONSE.md`)  
- [ ] Signed WFP callout / kernel divert driver (still requires external signing pipeline)  
- [ ] External third-party audit **engagement** (process ready; firm TBD)  

## Phase 7 — Neon Collar → **v1.0.0 stable**

- [x] **Fail-closed correctness** — empty chain refuses clearnet; no silent first-hop fallback  
- [x] Status: `fail_closed_tripped`, `refuse_direct`, `refused_connects`  
- [x] Health loop elapsed-timer (not wall-clock modulo)  
- [x] `trench doctor` self-test with exit codes + `trench first-run` wizard  
- [x] Control plane mutations: activate, legal, newnym, sessions, doctor, cloak up (subprocess)  
- [x] Command Nexus 2.0 — modular GUI, real hop map, one-click profiles, dossiers, a11y basics  
- [x] Serve `gui/web` from `trench gui` (no dist required)  
- [x] Landing recomposition + expanded threat education (how-it-works, FAQ, Nexus shot)  
- [x] Production install scripts default to non-dev extras (`TRENCH_DEV` opt-in)  
- [x] Plain-language WHAT_THIS_DOES / HOW_THE_CLOAK_WORKS / threat model + audit materials  
- [x] **Shipped as v1.0.0** (stable Neon Collar)  
- [ ] Windows hard KS Tor egress allow-list polish (post-1.0)  
- [ ] pipx / published wheel first-class docs path (post-1.0)  
