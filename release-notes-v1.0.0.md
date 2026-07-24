# Trench Coat v1.0.0 — Neon Collar

**Legal-first multi-hop privacy cloak** · AGPL-3.0-or-later  
**Site:** https://trenchcoat.jonbailey.xyz/  
**Source:** https://github.com/Pitchfork-and-Torch/trench-coat  

## What this release is

First **stable** release for careful operators: journalists, researchers, activists, and privacy-conscious professionals who need a **local SOCKS multi-hop orchestrator** with fail-closed defaults—not a crime toolkit and not a Tor Browser replacement.

## Highlights

- **Fail-closed that holds:** dead hops refuse CONNECT on `socks5://127.0.0.1:1080` (no silent clearnet via the cloak).
- **First-run + doctor:** guided legal accept, Tor detect, self-test with exit codes.
- **Command Nexus 2.0:** live hop map, one-click profiles, dossiers, clear CLOAKED / HOLD status.
- **Education:** plain-language “what this does / does not,” diagrams, threat model, hardening + audit readiness.
- **Local-first:** no mandatory cloud; telemetry opt-in only.

## Install (operator)

```bash
git clone https://github.com/Pitchfork-and-Torch/trench-coat.git
cd trench-coat
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1
source .venv/bin/activate
pip install -e .
trench first-run --accept-legal
```

Start **Tor** (9050 or Tor Browser 9150), then:

```bash
trench up --accept-legal --wait-tor 60
trench check-ip
trench gui
```

Point apps at: `socks5://127.0.0.1:1080`

## Doctor says “do not trust”?

Usually **Tor is not running**. Casual Shadow needs a live Tor SOCKS hop.

```text
# Windows (Tor Browser installed)
.\scripts\start-tor.ps1
# or start Tor Browser, then:
trench tor status
trench doctor
trench up --accept-legal --wait-tor 60
```

IPv6 warnings are hygiene tips, not the primary blocker.

## What 1.0 does **not** claim

- Whole-OS VPN without opt-in hard kill-switch  
- Browser fingerprint protection  
- Signed Windows WFP kernel isolation (still deferred)  
- Perfect anonymity or safety for illegal use  

## License & legal

AGPL-3.0-or-later. Legitimate privacy only. You own compliance with local law. Run `trench legal`.

## Support

Issues: GitHub Issues on the public repo. Security: see `SECURITY.md` (private disclosure for leak/fail-closed bypasses).
