# What Trench Coat does — and does **not** do

*Plain language for careful non-experts. Legal-first privacy tool.*

---

## In one sentence

**Trench Coat is a local “coat rack” for privacy hops:** your apps hang their traffic on a local door (`socks5://127.0.0.1:1080`), and Trench Coat walks that traffic through a chain of tunnels (often Tor) so websites and networks see less of your real location.

It is **not** a magic invisibility spell, a crime toolkit, or a replacement for good judgment.

---

## What it **does** (when used correctly)

| It does this | What that means for you |
|--------------|-------------------------|
| Runs a **local SOCKS entry** | Apps you configure to use `127.0.0.1:1080` go through the cloak |
| **Chains hops** | Traffic can go through more than one relay (e.g. VPN SOCKS → Tor) |
| **Auto-detects Tor** | Looks for Tor on ports 9050/9150 and can bind Tor hops |
| **Fail-closed by default** | If the hop chain dies, new connections via the cloak are **refused** — not silently sent as “you” on the open internet |
| Offers **profiles** | Casual Shadow, Ghost, Journalist, etc. — different risk/latency tradeoffs |
| Helps you **check identity** | `trench check-ip` asks “Does the Tor Project see me as Tor?” |
| Optional **hard kill-switch** | Advanced OS firewall rules (with an undo script written first) |
| Stays **local-first** | No mandatory cloud account; no silent product telemetry |

---

## What it does **not** do

| It does **not** do this | Why it matters |
|-------------------------|----------------|
| Replace **Tor Browser** | Tor Browser isolates *browsing*. Trench Coat chains *network hops* for apps you point at SOCKS |
| Cloak **every app automatically** | Soft mode only covers apps that use the local SOCKS. A browser that ignores the proxy still uses your real path |
| Stop **malware** on your computer | If your device is compromised, privacy tools cannot save you |
| Hide you from **browser fingerprinting** alone | Canvas, fonts, logins, and behavior can still identify you |
| Make illegal activity **safe or legal** | Legal-first tool. You must follow the law where you are |
| Defeat a **nation-state with full device access** | Out of scope. No honest tool claims this |
| Guarantee **perfect anonymity** | Multi-hop reduces some observers; it does not erase all risk |
| Ship a **signed Windows kernel firewall driver** yet | Hard isolation today uses user-level scripts (netsh/nft/pf). WFP callout is future work |

---

## Simple picture: path of a request

```text
  YOU + YOUR APP
        │
        │  (must be set to use the cloak)
        ▼
  ┌─────────────────────────┐
  │  Trench Coat entry      │
  │  socks5://127.0.0.1:1080│
  │  on YOUR computer only  │
  └───────────┬─────────────┘
              │
              ▼
        Hop 1 (e.g. VPN SOCKS)
              │
              ▼
        Hop 2 (e.g. Tor)
              │
              ▼
        Open internet / website
        (sees hop exit, not home IP
         — if everything is healthy)
```

**Fail-closed (important):**

```text
  If hops die:
        App ──► Trench entry ──► REFUSED
                                (no quiet leak as “home IP”
                                 through the cloak port)
```

Apps that **never** used the cloak still go direct. That is normal soft-mode behavior — not a bug in the refusal logic.

---

## Who sees what? (everyday language)

```text
  ┌──────────────┐     can see you connect to first hop
  │ Wi‑Fi / ISP  │ ──► (not every website name, if DNS is careful)
  └──────────────┘

  ┌──────────────┐     can see traffic next to them
  │ A middle hop │ ──► (not always the full path)
  └──────────────┘

  ┌──────────────┐     sees the EXIT address + your browser/app style
  │ The website  │ ──► (not your home address IF cloak + Tor healthy)
  └──────────────┘

  ┌──────────────┐     can see EVERYTHING
  │ Malware on PC│ ──► Trench Coat cannot fix this
  └──────────────┘
```

---

## Soft coat vs hard collar

| Mode | Everyday metaphor | Default |
|------|-------------------|---------|
| **Soft** | “Only people who use *this door* wear the coat.” Apps must use SOCKS. Dead chain → door locks (refuses). | Normal default |
| **Hard** (opt-in) | “Also lock the other exits on the building.” OS firewall. Can lock you out if misused. Undo script first. | Off until you confirm |

---

## Quick trust checklist

1. `trench first-run --accept-legal`  
2. Start Tor (or your first hop).  
3. `trench doctor` — fix red fails.  
4. `trench up --accept-legal --wait-tor 60`  
5. `trench check-ip` — want `IsTor: true` when Tor is the exit.  
6. Point **only the apps you intend** at `socks5://127.0.0.1:1080`.  
7. Optional GUI: `trench gui` → http://127.0.0.1:8742  

---

## Legal spine (non-negotiable)

Trench Coat is for **legitimate privacy**: reducing casual tracking, resisting censorship, protecting journalists, researchers, and ordinary people.

**Do not** use it to commit crimes, harass people, commit fraud, or evade lawful process. Run `trench legal` any time.

---

## Read next

| Doc | Best for |
|-----|----------|
| [HOW_THE_CLOAK_WORKS.md](HOW_THE_CLOAK_WORKS.md) | Step-by-step + diagrams |
| [THREAT_MODEL.md](dossiers/THREAT_MODEL.md) | Who might attack what |
| [HARDENING.md](security/HARDENING.md) | Operator checklist |
| Landing | https://trenchcoat.jonbailey.xyz/ |
