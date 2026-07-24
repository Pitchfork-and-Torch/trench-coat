# Residual roadmap — Iron Collar & packaging

*What is still open after Neon Collar **v1.0.0**. Honest scope for operators and auditors.*

## Done in 1.0 (do not re-list as gaps)

- Fail-closed refuse-direct at SOCKS entry  
- No silent first-hop fallback (`allow_partial_chain` default false)  
- Doctor self-test + first-run wizard  
- Command Nexus 2.0 (status, map, profiles, dossiers)  
- Plain-language threat / how-it-works docs  
- Hardening + audit readiness updated  

## Residual Phase 6 — Iron Collar

| Item | Priority | Notes |
|------|----------|-------|
| Windows hard KS + Tor egress | P1 | Ensure Tor process can still reach relays under hard rules; document program allow-list |
| Hard KS residual rule detection in doctor | P2 | Warn if TrenchCoat firewall rules still present after disarm |
| Signed WFP / kernel divert | P3 / external | Requires EV signing pipeline; see `packaging/windows-wfp-notes.md` |
| Third-party audit firm engagement | P2 | Materials ready; firm TBD |
| Auto hard KS on hop death | **Won’t do by default** | Lockout risk; only via future explicit user policy if ever |

## Packaging / first-run (post-1.0 polish)

| Item | Priority | Notes |
|------|----------|-------|
| pipx one-liner as primary docs path | P1 | Keep git+venv as advanced |
| PyInstaller onedir + checksums | P2 | Expand `packaging/trenchcoat.spec` |
| Signed Windows/macOS installers | P3 | Only when signing pipeline exists |
| Tauri desktop shell | P3 | Scaffold only today |

## Command Nexus / ecosystem

| Item | Priority | Notes |
|------|----------|-------|
| Richer chain builder UI | P2 | Templates + drag reorder |
| In-process cloak up without dual engines | P2 | Safer lifecycle than subprocess |
| Browser extension badge from identity API | P2 | Keep separate trust domain |
| Deeper Ghost Continuum plane | P3 | Continuum repo owns plane UX |

## Documentation hygiene

| Item | Priority | Notes |
|------|----------|-------|
| Keep HARDENING / THREAT_MODEL / audit checklist in sync with code | Standing | Every isolation change |
| Release notes: capability **and** responsibility | Standing | Template in CHANGELOG |

## Success criteria mapping

| Criterion | 1.0 status |
|-----------|------------|
| New user guided flow → verify Tor | **Met** (first-run, doctor, check-ip) |
| Nexus feels professional | **Met** (MVP 2.0; polish ongoing) |
| Fail-closed clearly communicated | **Met** (docs + GUI HOLD + status fields) |
| Landing/docs build trust | **Met** (what/how/threat) |
| Legal-first AGPL | **Met** |
| Non-dev packaging | **Partial** (install scripts; pipx/sign later) |
| Iron Collar residual scoped | **Met** (this doc) |
