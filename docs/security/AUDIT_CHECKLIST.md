# Security Audit Checklist

Use before tagging a release. Mark each item Pass / Fail / N/A.  
**Aligned with 1.0 Neon Collar.**

Auditor: __________  Date: __________  Version: __________

---

## Legal & product

- [ ] README and CLI legal notice present and accurate  
- [ ] First-run / `--accept-legal` gate blocks engage without acceptance  
- [ ] No modules primarily useful for crime (exploit, spam, credential theft)  
- [ ] Default configs do not enable community sharing or telemetry  
- [ ] Landing + docs remain legal-first (no “evade law enforcement” language)

## Network & fail-closed

- [ ] Fail-closed when hop list empty at **start** (cloak not engaged)  
- [ ] Fail-closed when hop list empty **mid-session** (CONNECT refused, no clearnet)  
- [ ] Multi-hop failure does not silent first-hop fallback (unless `allow_partial_chain`)  
- [ ] Tests cover refuse-direct (`tests/test_fail_closed.py` green)  
- [ ] Local SOCKS binds loopback by default  
- [ ] Control API binds loopback by default  
- [ ] Documented DNS leak guidance reviewed  
- [ ] IPv6 risk documented / mitigated where possible  
- [ ] Soft vs hard kill-switch documented honestly per platform  

## Kill-switch (Iron Collar)

- [ ] Soft refuse-direct aligns with fail_closed policy  
- [ ] Hard mode writes undo **before** apply  
- [ ] Hard mode requires `--confirm`  
- [ ] Dry-run does not apply rules  
- [ ] Disarm / undo path documented  
- [ ] No auto hard-firewall on hop death  
- [ ] Windows / Linux / macOS script emitters present  
- [ ] Residual: signed WFP marked **not shipped** in user-facing docs  

## Cryptography & secrets

- [ ] No secrets in git  
- [ ] Proxy credentials not logged at INFO  
- [ ] Session exports free of plaintext passwords  

## Dependencies

- [ ] `pip audit` / OSV clean or risks accepted in writing  
- [ ] Lockfile or pinned versions for release artifacts  
- [ ] GitHub Actions use pinned action SHAs (stretch)  

## Code quality

- [ ] Unit tests green (`pytest -q`)  
- [ ] No `eval` / shell injection in hop config paths  
- [ ] Subprocess calls use argument lists, not `shell=True` where avoidable  

## Platform & packaging

- [ ] Windows install path documented  
- [ ] Linux install path documented  
- [ ] macOS install path documented  
- [ ] Privilege requirements documented per feature  
- [ ] Install scripts default to non-dev extras  
- [ ] `trench first-run` and `trench doctor` documented  

## GUI / in-app guidance

- [ ] No external CDN requirements for core UI  
- [ ] No analytics by default  
- [ ] XSS-safe rendering of hop labels / dossier text  
- [ ] Foot-gun guidance visible (proxy requirement, soft vs hard, fail-closed)  
- [ ] Status shows fail-closed / HOLD clearly  

## Observability & confidence

- [ ] Session dossiers listable without leaking secrets  
- [ ] Doctor exit codes meaningful (0/1/2)  
- [ ] Platform isolation capability reported  

## Incident readiness

- [ ] SECURITY.md contact path works  
- [ ] Known limitations listed in HARDENING.md  
- [ ] THREAT_MODEL.md claims match code  
- [ ] THIRD_PARTY_AUDIT.md residual table current  

---

## Sign-off

| Role | Name | Result |
|------|------|--------|
| Maintainer | | Pass / Fail |
| Independent reviewer (if any) | | Pass / Fail |

Notes:
