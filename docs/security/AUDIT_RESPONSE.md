# Third-party audit — engagement & findings response

Part of **Phase 6 Iron Collar**. Use this when commissioning an external security review of Trench Coat.

## Scope (suggested)

| In scope | Out of scope |
|----------|----------------|
| CLI / engine / hop chain / kill-switch | Operator OPSEC mistakes |
| Local control API (loopback) | Tor network itself |
| Soft/hard routing scripts | Third-party hop daemons (sslocal, hy2, wireguard) binary supply chain beyond pin notes |
| GUI web nexus XSS / CSRF on loopback | Full malware analysis of Tor Browser |

## Engagement checklist

1. Freeze a **tagged release** and publish `git archive` + checksums.  
2. Share [THIRD_PARTY_AUDIT.md](THIRD_PARTY_AUDIT.md) and [HARDENING.md](HARDENING.md).  
3. Provide a non-root VMs snapshot with Tor + `trench doctor` green.  
4. Agree **safe harbor**: no intentional production hard kill-switch without undo validation.  
5. Expect findings as: Critical / High / Medium / Low / Informational.

## Public response template

```markdown
## Audit response — Trench Coat <version>

**Auditor:** <firm or researcher>  
**Report date:** YYYY-MM-DD  
**Scope:** <tag or commit>

### Summary

We thank <auditor> for reviewing Trench Coat. We take fail-closed routing and
local-first privacy seriously.

### Findings

| ID | Severity | Status | Notes |
|----|----------|--------|-------|
| TC-001 | … | Fixed in <tag> / Accepted risk / Deferred | … |

### Fixed

- …

### Accepted risk

- …

### Deferred

- …

MIT/AGPL notice: Trench Coat remains AGPL-3.0-or-later. Audit does not change license.
```

## Hard kill-switch audit notes

- Hard mode is **opt-in** (`trench killswitch hard --confirm`).  
- Undo scripts are written **before** apply under `~/.trenchcoat/killswitch/`.  
- Default CLI without `--confirm` is dry-run.  
- Full transparent WFP callout drivers remain out of tree; see packaging hard scripts.

## Contact

Security issues: see [SECURITY.md](../../SECURITY.md). Do not open public issues for exploitable vulns before a fix window.
