# Changelog

## Unreleased

### Fixed
- Disengage (`stop_owner`) refuses to signal a recycled OS PID that is not a trench process; clears the stale lock instead.

## 1.3.0 - Hop Receipt

Local `trench receipt --json` prints chain hop types and enabled flags. Passwords and endpoints stay out of the receipt.

Infographic and public version stamps: **1.3.0**.

Trench Coat is a legal-first Tor-aware multi-hop privacy cloak: CLI core, local SOCKS chaining, Tor-aware profiles, split-tunnel and system routing helpers, managed hop drivers (external clients), plugins, optional decoy traffic, optional Ghost Continuum companion plane, and a Command Nexus control surface.

## 1.2.1 - Circuit Desk (honesty)

Copy and version stamps aligned with shipped behavior. No new hops, hosts, or attack surface.

### Honesty

- Version **1.2.1** in package metadata, `trench --version`, Nexus tagline, landing/AEO, and docs alignment stamps.
- README lead: legal-first Tor-aware cloak; explicit **not** a VPN, Tor Browser, I2P client, or crime toolkit.
- Capability table: I2P is stub-only; SS/Hy2/WG need an installed client + SOCKS bridge; Tauri is scaffold; telemetry is local-file only; Ghost Continuum is an optional companion repo.
- Architecture hop table no longer calls managed SS/Hy2/WG "stub."
- Telemetry FAQ: no upload. SECURITY.md lists 1.2.x as supported.
- Landing mojibake (`→`) and Twitter handle mismatch (`@suddenlyjon`) fixed.
- CLI banner help is no longer "neon"; tagline is "legal-first privacy cloak."

### Responsibility

Legal-first only. Not a crime toolkit. Fail-closed and `--accept-legal` unchanged.

## 1.2.0 - Circuit Desk

Command Nexus becomes a hop workshop. Velvet Collar visual system unchanged.

### Circuit Desk

- Hop strip in Nexus: enable, reorder, drop, label, add hop. Templates import Casual Tor / Journalist Field / VPN-then-Tor without YAML.
- `GET`/`PUT /api/chain`, `GET /api/templates`, `POST /api/templates/{id}/import`. Passwords never leave the API in GET bodies.
- City map draws the draft circuit before Engage, then live hop telemetry after.

### Cloak lifecycle

- Pid lock so GUI and CLI cannot both own the SOCKS data plane.
- `POST /api/cloak/down` stops the Engage subprocess (no more "hint: Ctrl+C in the other terminal").
- Fail-closed: empty or under-min enabled hops cannot persist or Engage.

### Responsibility

Legal-first only. Not a crime toolkit. Dual engines still forbidden: CLI owns the data plane; Nexus is control plane.

## 1.1.0 - Velvet Collar

Major branding + residual Iron Collar polish. Core engine and fail-closed guarantees unchanged (no breaking CLI behavior).

### Brand and product surface

- Full **Velvet Collar** visual system: film-noir watercolor (midnight indigo, parchment, sage, gold). Neon cyan/magenta retired.
- Brand documentation: `docs/BRAND.md`.
- Public landing rebuilt (`landing/`): glass panels, scroll reveals, reduced-motion rain ambient, Fontshare self-host.
- New illustrated assets + OG card (`og-card.png` + `og.jpg`).
- Velvet marketing shots: `command-nexus-velvet.png` (recolored Nexus proof) + `how-cloak-works-velvet.png` (exact-label hop diagram).
- Command Nexus theme harmonized to Velvet tokens (functionality preserved).

### Residual Iron Collar / confidence

- Doctor: **`hard_ks_residual`** warns if leftover hard kill-switch OS rules remain after disarm.
- Doctor / hard plan: Windows **Tor egress allow-list** guidance; hard apply adds program-allow rules for detected `tor.exe` paths.
- Hardening guide expanded (`docs/security/HARDENING.md`).

### Packaging / first-run docs

- **pipx** documented as the primary recommended install path on the landing and README.

### Responsibility

Legal-first only. Not a crime toolkit. Soft mode cloaks apps pointed at SOCKS; hard kill-switch remains opt-in with undo-first scripts.

## 1.0.0 - Neon Collar (first stable)

First **stable** release. Capability and responsibility both matter: multi-hop privacy for legitimate use, fail-closed by default, clear threat limits.

### Security / fail-closed (critical)

- **Empty hop chain no longer dials clearnet** through the local SOCKS entry when `fail_closed` is on (`refuse_direct`).
- Multi-hop failure no longer silently falls back to first-hop-only unless `policy.allow_partial_chain` is true.
- Mid-session hop death sets `fail_closed_tripped` and keeps the entry refusing CONNECTs.
- Health rebuild uses an elapsed timer (not wall-clock modulo).
- Status exposes `fail_closed_tripped`, `refuse_direct`, `refused_connects`.

### Confidence UX

- `trench doctor` - structured self-test with exit codes (0/1/2), `--json`, actionable failure summaries.
- Pre-flight: cloak not listening yet is **info**, not a hard fail (start Tor / hops first).
- `trench first-run --accept-legal` - legal → profile → Tor detect → doctor → next steps.
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

## 0.6.0 - Neon Collar (pre-stable track)

Internal/dev track of the same feature set prior to 1.0 version lock. Superseded by 1.0.0.

## 0.5.0 - Syndicate

Phases 0 - 5 complete: multi-hop chain, Tor detect, profiles, dossiers, GUI, split-tunnel, managed hops, optimizer, templates, opt-in telemetry, landing. Phase 6 Iron Collar (hard kill-switch scripts) largely done; signed WFP deferred.
