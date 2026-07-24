# Third-Party Security Audit Readiness

**Product:** Trench Coat — legal-first multi-hop privacy cloak  
**Aligned version:** 1.0.x Neon Collar  
**License:** AGPL-3.0-or-later  

Trench Coat is legal-first privacy software. This document prepares the project for an independent security review and keeps residual Iron Collar items explicit.

---

## 1. Scope recommended for auditors

| Area | Paths | Risk focus |
|------|-------|------------|
| Local SOCKS entry | `src/trenchcoat/engine/proxy_server.py` | Open proxy abuse, **fail-closed**, no silent clearnet |
| Nested hop chaining | `engine/chain.py`, `hops/` | Dead-hop exclusion, partial-chain policy |
| Engine orchestration | `engine/router.py` | Hop-death refuse mode, health cadence |
| Kill-switch / routing | `engine/killswitch.py`, `system_route.py` | Lockout, incomplete isolation, undo-first |
| Config & secrets | `config/`, platformdirs paths | Credential storage, path traversal |
| Control API | `api/server.py` | Loopback-only assumption, unauthenticated localhost POSTs |
| Self-test | `engine/self_test.py` | Accuracy of confidence signals |
| Plugins | `plugins/`, `plugins/base.py` | Untrusted code load surface |
| Telemetry | `reporting/telemetry.py` | Opt-in only; no PII/IPs |
| GUI / extension | `gui/web/`, `browser_extension/` | XSS of hop labels, foot-gun UX |

---

## 2. Explicit non-goals (in scope honesty)

- No offensive exploit modules  
- No “evade law enforcement” features  
- No automatic hard firewall without operator `--confirm`  
- No claim of signed WFP / kernel divert until a signed pipeline exists  
- No mandatory cloud or product telemetry  

---

## 3. Critical invariants (must hold)

| ID | Invariant | Test / evidence |
|----|-----------|-----------------|
| FC-1 | Empty `proxy_chain` + `refuse_direct` ⇒ CONNECT fails, no clearnet | `tests/test_fail_closed.py` |
| FC-2 | Start with zero live hops + `fail_closed` ⇒ not running | same + doctor |
| FC-3 | Multi-hop failure does not first-hop fallback unless `allow_partial_chain` | unit + policy default false |
| KS-1 | Hard arm writes undo **before** apply | `tests/test_killswitch.py` |
| KS-2 | Hard apply requires confirm | same |
| NET-1 | Default listen host is loopback | config defaults |
| TEL-1 | Telemetry off by default | config + telemetry tests |

**Regressions that must block release:** any reintroduction of empty-chain direct dial.

---

## 4. Build & test for auditors

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pytest -q
ruff check src tests
trench doctor --no-identity
```

Suggested manual probes:

1. Engage with Tor → `trench check-ip` → IsTor true.  
2. Stop Tor mid-session → CONNECT via `:1080` must fail (not home IP).  
3. Hard KS dry-run → undo path exists under `~/.trenchcoat/killswitch/`.  
4. Control API only on 127.0.0.1; GUI XSS check on hop labels.

---

## 5. Threat model & hardening

| Doc | Use |
|-----|-----|
| `docs/dossiers/THREAT_MODEL.md` | Adversaries, claims, non-claims |
| `docs/WHAT_THIS_DOES.md` | Non-expert summary |
| `docs/HOW_THE_CLOAK_WORKS.md` | Diagrams |
| `docs/security/HARDENING.md` | Operator runbook |
| `docs/security/AUDIT_CHECKLIST.md` | Release gate checklist |
| `docs/security/AUDIT_RESPONSE.md` | Template for public findings response |
| `SECURITY.md` | Disclosure channel |

---

## 6. Known residual risks (Iron Collar / packaging)

| Item | Status | Notes for auditors |
|------|--------|--------------------|
| Signed Windows WFP callout | **Open** | See `packaging/windows-wfp-notes.md` |
| Windows hard KS vs Tor egress | **Partial** | netsh loopback allow-list can starve Tor’s own outbound; operator must test |
| Soft mode whole-OS | **N/A by design** | Documented limitation |
| GUI engage via subprocess | **MVP** | Data plane still owned by `trench up`; race/docs clarity |
| Plugin loading | **Trust boundary** | Local plugins = code execution as user |
| External firm engagement | **TBD** | Checklist ready; firm not engaged |

---

## 7. Status checklist

- [x] Audit checklist published  
- [x] Fail-closed tests for refuse-direct / hop death  
- [x] Hard KS undo-first tests  
- [x] Threat model + plain-language docs  
- [x] Hardening guide current for 1.0  
- [ ] External firm engagement (community / sponsor)  
- [ ] Public findings response (after engagement)  
- [ ] Signed WFP pipeline (separate milestone)  

---

## 8. Reporting

Follow `SECURITY.md` for private vulnerability disclosure.  
Priority issues: fail-closed bypass, kill-switch lockout without undo, remote API exposure, credential leakage in logs.
