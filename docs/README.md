# Trench Coat documentation

**Legal-first multi-hop privacy cloak** · AGPL-3.0-or-later · [Landing](https://trenchcoat.jonbailey.xyz/)

## Start here (non-experts)

| Doc | Why |
|-----|-----|
| [WHAT_THIS_DOES.md](WHAT_THIS_DOES.md) | What the cloak does / does **not** do |
| [HOW_THE_CLOAK_WORKS.md](HOW_THE_CLOAK_WORKS.md) | Diagrams, packet path, foot-guns |
| [dossiers/THREAT_MODEL.md](dossiers/THREAT_MODEL.md) | Who might observe you; honest limits |
| Landing | Cinematic overview + FAQ |

## Operators

| Doc | Why |
|-----|-----|
| [security/HARDENING.md](security/HARDENING.md) | Checklist, kill-switch, DNS/IPv6 |
| [architecture/OVERVIEW.md](architecture/OVERVIEW.md) | Components & trust boundaries |
| [architecture/SYSTEM_ROUTING.md](architecture/SYSTEM_ROUTING.md) | Soft route / hard scripts |
| [GHOST-CONTINUUM.md](GHOST-CONTINUUM.md) | Optional `trench-cloak` plane |
| [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) | Phases 0–7 + residual roadmap |

## Security & audit

| Doc | Why |
|-----|-----|
| [security/THIRD_PARTY_AUDIT.md](security/THIRD_PARTY_AUDIT.md) | Auditor onboarding |
| [security/AUDIT_CHECKLIST.md](security/AUDIT_CHECKLIST.md) | Pre-release gate |
| [security/AUDIT_RESPONSE.md](security/AUDIT_RESPONSE.md) | Findings response template |
| `../SECURITY.md` | Vulnerability disclosure |

## AEO / marketing

| Doc | Why |
|-----|-----|
| [AEO.md](AEO.md) | Answer-engine copy |
| `../landing/` | Production site source |

## CLI confidence path

```text
trench first-run --accept-legal
trench doctor
trench up --accept-legal --wait-tor 60
trench check-ip
trench gui
```
