# Changelog

Trench Coat is a legal-first multi-hop privacy cloak: CLI core, local SOCKS chaining, Tor-aware profiles, split-tunnel and system routing helpers, managed hop drivers, plugins, decoy traffic, Ghost Continuum plane integration, and a cyberpunk control nexus.

## 1.0.0 — Neon Collar (first stable)

First **stable** release. Capability and responsibility both matter: multi-hop privacy for legitimate use, fail-closed by default, clear threat limits.

### Security / fail-closed (critical)

- **Empty hop chain no longer dials clearnet** through the local SOCKS entry when `fail_closed` is on (`refuse_direct`).
- Multi-hop failure no longer silently falls back to first-hop-only unless `policy.allow_partial_chain` is true.
- Mid-session hop death sets `fail_closed_tripped` and keeps the entry refusing CONNECTs.
- Health rebuild uses an elapsed timer (not wall-clock modulo).
- Status exposes `fail_closed_tripped`, `refuse_direct`, `refused_connects`.

### Confidence UX

- `trench doctor` — structured self-test with exit codes (0/1/2), `--json`, actionable failure summaries.
- Pre-flight: cloak not listening yet is **info**, not a hard fail (start Tor / hops first).
- `trench first-run --accept-legal` — legal → profile → Tor detect → doctor → next steps.
- Control API mutations: legal accept, chain activate, Tor NEWNYM, sessions, doctor, cloak up (subprocess).
- Command Nexus 2.0: modular GUI, real hop labels on city map, one-click profiles, dossier viewer, action bar, reduced-motion support.
- `trench gui` serves `gui/web` without a separate dist build.

### Education & trust

- Plain-language docs: `docs/WHAT_THIS_DOES.md`, `docs/HOW_THE_CLOAK_WORKS.md` (diagrams), expanded threat model.
- Hardening guide + third-party audit readiness aligned to fail-closed invariants.
- Landing: Nexus proof shot, how-it-works, expanded FAQ, observer table.
- Residual Iron Collar roadmap documented (`docs/ROADMAP_RESIDUAL.md`).

### Packaging

- Install scripts default to production extras (`TRENCH_DEV=1` for dev deps).

### Residual (not blocking 1.0)

- Signed Windows WFP callout / kernel divert (external signing track).
- Windows hard KS Tor egress polish; pipx-first published wheel; Tauri desktop shell.

### Responsibility

Legal-first only. Not a crime toolkit. Soft mode cloaks apps pointed at SOCKS; hard kill-switch is opt-in with undo-first scripts. See `trench legal`, `docs/WHAT_THIS_DOES.md`, and `docs/dossiers/THREAT_MODEL.md`.

## 0.6.0 — Neon Collar (pre-stable track)

Internal/dev track of the same feature set prior to 1.0 version lock. Superseded by 1.0.0.

## 0.5.0 — Syndicate

Phases 0–5 complete: multi-hop chain, Tor detect, profiles, dossiers, GUI, split-tunnel, managed hops, optimizer, templates, opt-in telemetry, landing. Phase 6 Iron Collar (hard kill-switch scripts) largely done; signed WFP deferred.
