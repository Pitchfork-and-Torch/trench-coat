# Hardening Guide — Trench Coat

*Put the coat on correctly or don’t bother.*  
**Updated for 1.0 Neon Collar** (fail-closed refuse-direct, first-run, doctor exit codes).

Plain-language companion: [WHAT_THIS_DOES.md](../WHAT_THIS_DOES.md) · [THREAT_MODEL.md](../dossiers/THREAT_MODEL.md)

---

## Baseline posture (do these every time)

1. Accept the legal notice only if your use is **lawful** (`trench legal` / `trench first-run --accept-legal`).  
2. Prefer **Casual Shadow** or **Ghost** until hops are real and healthy.  
3. Run `trench doctor` after every config change (exit `2` = do not trust yet).  
4. Keep the control API on `127.0.0.1` only (`trench gui`).  
5. Update Tor / VPN clients independently; Trench Coat **orchestrates**, it does not replace vendor security.  
6. Point **only intended apps** at `socks5://127.0.0.1:1080`. Soft mode does not cloak the whole OS.  
7. Verify with `trench check-ip` before high-risk work (`IsTor: true` when Tor is egress).

---

## Fail-closed (v0.6+) — read this

| Situation | Expected behavior |
|-----------|-------------------|
| Engage with zero live hops | Cloak **does not** start (fail-closed message) |
| All hops die mid-session | Entry stays up but **refuses** new CONNECTs; status `fail_closed_tripped` |
| Multi-hop nest fails | No silent “first hop only” unless `allow_partial_chain: true` |
| App never used SOCKS | Still goes clearnet — configure the app |

Counters: `refused_connects` on status / Command Nexus.

**Do not** set `fail_closed: false` unless you fully understand clearnet risk.

---

## DNS

- Prefer **remote DNS** through SOCKS (`--socks5-hostname`, apps that resolve remotely).  
- Avoid ISP DNS while cloaked.  
- `trench doh` only helps if the DoH peer is reached *through* the chain.  
- Doctor and DNS guard emit recommendations; they are not a full leak lab.

---

## IPv6

- If the chain is IPv4-only, **disable IPv6** on the active interface or block it in the firewall.  
- AAAA / IPv6 surprises are a classic coat tear.  
- Use `trench ipv6` / doctor recommendations as a starting point, then verify on your OS.

---

## WebRTC / browser

- Disable WebRTC or use a hardened browser profile.  
- Prefer **separate browser profiles** for cloaked vs clearnet work.  
- Fingerprinting (canvas, fonts, WebGL) is **not** solved by proxying alone.  
- For high-risk browsing, prefer **Tor Browser** over “random browser + SOCKS”.

---

## Kill-switch

### Soft (default product path)

- Apps must use the local SOCKS entry — non-proxied apps still leak.  
- Soft arm + `fail_closed` refuse direct dials at the SOCKS layer (v0.6+).  
- Message-only “soft arm” without refuse-direct is **not** the trust model anymore.

### Hard (opt-in Iron Collar)

```text
trench killswitch hard --dry-run     # writes undo first, no apply
trench killswitch hard --confirm     # apply after you understand undo
trench killswitch disarm             # best-effort cleanup
trench killswitch scripts            # emit reviewable bundles
```

| Platform | Mechanism today | Notes |
|----------|-----------------|-------|
| Windows | `netsh advfirewall` allow-list + block outbound | Admin required; can interfere with Tor’s own egress — test carefully; **signed WFP not shipped** |
| Linux | nftables table drop policy + lo/established | Strongest of the three script paths |
| macOS | pf anchor | Root; keep disable recipe next to enable |

**Safety rules (non-negotiable):**

1. Undo script is written **before** any hard apply.  
2. `--confirm` required for apply; prefer dry-run first.  
3. **Never** auto-apply hard firewall on hop death (lockout risk).  
4. Keep a recovery path (local console, known undo path under `~/.trenchcoat/killswitch/`).

---

## Hop selection

- Do not put your only trust in a single commercial VPN.  
- Diversify jurisdictions **and** operators.  
- Self-hosted hops: patch, key-only SSH, no reused passwords.  
- Residential proxies: ensure **legitimate** authorization; stolen residential bots are unethical and often illegal.  
- Prefer Tor as last hop when your threat model wants Tor egress identity.

---

## Logs & dossiers

- Session dossiers (JSON/HTML) can include operational events — treat as sensitive.  
- Restrict filesystem ACLs; do not sync dossiers to third-party cloud without encryption you control.  
- `encrypt_logs` config flag: respect intent; still assume local disk can be seized.

---

## Supply chain

- Install from the official GitHub repo / release artifacts you verify.  
- Prefer `pip install -e .` or pinned release wheels; use `TRENCH_DEV=1` only when developing.  
- Run `pytest -q` before relying on local builds.  
- For auditors: see [THIRD_PARTY_AUDIT.md](THIRD_PARTY_AUDIT.md).

---

## Platform isolation matrix (honest)

| Capability | Windows | Linux | macOS |
|------------|---------|-------|-------|
| Soft SOCKS cloak | Yes | Yes | Yes |
| Fail-closed refuse-direct | Yes | Yes | Yes |
| Hard KS scripts (opt-in) | netsh | nft | pf |
| Signed kernel WFP / divert | **No** (deferred) | N/A | N/A |
| Whole-OS without hard KS | **No** | **No** | **No** |

Doctor reports a one-line platform isolation capability check.

---

## Linux nftables / Windows / macOS sketches

Operator-applied examples live under `packaging/` and `trench killswitch scripts`.  
**EXAMPLE ONLY** — adapt; never paste blindly on production hosts. Always keep the disable path.

---

## Foot-gun checklist (print this)

- [ ] Legal accepted for lawful use only  
- [ ] Tor/VPN hop actually running before `trench up`  
- [ ] `trench doctor` exit 0 or understood warnings  
- [ ] Apps proxy settings verified (not just “cloak running”)  
- [ ] `trench check-ip` matches expectations  
- [ ] Hard KS dry-run + undo path known **before** confirm  
- [ ] IPv6 / DNS / WebRTC considered for browser work  
- [ ] Dossiers not left on shared machines  

---

## Incident / leak response

1. Stop high-risk work.  
2. `trench doctor` + check Command Nexus fail-closed / hop health.  
3. If hard KS applied: run undo script first if locked out.  
4. Rotate identities/accounts if you believe clearnet exposure occurred.  
5. Report product bugs privately per `SECURITY.md` (especially fail-closed bypasses).
