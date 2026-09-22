# Trench Coat 1.3.2 - Companion status

The optional browser companion no longer says Cloaked whenever `/api/status` has `running`.

- Pending, stale, fail-closed, a dead hop, or a port with no owner stay not cloaked.
- A degraded hop says Degraded and names the listener. It does not say Cloaked.
- The proxy button stays off until a cloak or a degraded listener is up, then uses that listen port on 127.0.0.1.

AGPL-3.0-or-later. https://trenchcoat.jonbailey.xyz/
