# Trench Coat 1.3.1 - Status Honesty

**Codename:** Circuit Desk
Patch: pid fingerprint Disengage + hop probe honesty. No new hops, hosts, or attack surface.

## Honesty

- Disengage matches `create_time` on the pid lock. Reused PIDs and legacy bare pid files are stale: lock cleared, process not killed.
- SOCKS5/HTTP hop probe: CONNECT refused to the probe dest is DEGRADED (listener up), not HEALTHY. Closed port is DEAD. DEGRADED hops stay chainable.
- `/api/status` does not paint CLOAKED from a listening port or a stale status bus. Engage can return pending (not cloaked yet) or 503 if the child exits.
- Command Nexus shows ENGAGING while the owner pid is alive and the entry is not up.

## Unchanged rails

Legal-first only. Fail-closed refuse-direct. `--accept-legal` required to engage. AGPL-3.0-or-later. No new outbound hosts.
