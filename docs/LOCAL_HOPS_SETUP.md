# Ghost / Journalist hop setup (Windows)

## What was configured

Local **lab SOCKS hops** so multi-hop chains work without a paid VPN yet:

| Port | Role | Used by |
|------|------|---------|
| `127.0.0.1:1088` | "VPN lab" intermediate SOCKS | Ghost (front), Journalist (mid) |
| `127.0.0.1:1081` | "Self-hosted lab" entry SOCKS | Journalist (first hop) |
| `127.0.0.1:9050` | Tor | All profiles (final hop) |

### Chains

- **Ghost:** `1088` → `9050` (Tor)
- **Journalist:** `1081` → `1088` → `9050` (Tor)
- **Casual Shadow:** Tor only (`9050`)

## Honest privacy note

Lab hops on loopback prove multi-hop plumbing and still **exit via Tor** (`IsTor: true`).  
They are **not** a real commercial VPN or remote VPS. Your first real network hop to the open internet for Tor circuits is still Tor's guards (unless you put a real VPN under Tor at the OS level).

To upgrade to real multi-operator hops later, edit hop host/port (and user/pass) in:

`%LOCALAPPDATA%\trenchcoat\trench-coat\config.yaml`

Examples:

- Mullvad SOCKS (account number as username, any password)
- Your VPS: `ssh -D 1081 user@vps` or a Shadowsocks/Hysteria local client

## Daily commands

```powershell
cd $env:USERPROFILE\trench-coat   # or your clone path

# Start lab SOCKS + Tor + cloak for a profile
$env:TRENCH_CHAIN = "ghost"   # or journalist / casual-shadow
powershell -ExecutionPolicy Bypass -File .\scripts\start-local-hops.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\start-tor.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\engage-windows.ps1

trench check-ip
# apps -> socks5://127.0.0.1:1080
```

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/local_socks_hop.py` | Minimal SOCKS5 hop process |
| `scripts/start-local-hops.ps1` | Start 1081 + 1088 (breakaway) |
| `scripts/configure_lab_hops.py` | Wire ghost/journalist config to lab ports |
| `scripts/engage-windows.ps1` | One-shot engage (starts lab hops for non-casual chains) |
