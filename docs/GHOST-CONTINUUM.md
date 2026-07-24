# Ghost Continuum integration

Trench Coat is registered as plane **`trench-cloak`** in [Ghost Continuum](https://github.com/Pitchfork-and-Torch/ghost-continuum).

## Why

| Ghost Continuum | Trench Coat |
|-----------------|-------------|
| Deception · detection · forensics | Privacy · multi-hop · fail-closed |
| Watches the wire | Leaves a thinner silhouette |

Together: immune fabric + invisibility cloak. Defensive only.

## Enable

In Ghost Continuum config:

```json
"planes": { "trenchCloak": true }
```

Run Trench Coat:

```bash
trench up --accept-legal
```

Arm the plane from the Nexus or `node bin/arm-planes.js`.

## What Continuum sees

- SOCKS entry listening (default 1080)
- Tor SOCKS 9050/9150
- Optional API identity (`IsTor`, version)

See Continuum doc: `docs/TRENCH-CLOAK-PLANE.md` in that repo.
