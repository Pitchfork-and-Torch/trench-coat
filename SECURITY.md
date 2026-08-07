# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 1.0.x | ✅ supported |
| 0.5.x / 0.6.x | best-effort (upgrade to 1.0) |

## Reporting a vulnerability

Email or private channel preferred. **Do not** file a public GitHub issue for:

- Remote code execution, privilege escalation, path traversal  
- Kill-switch bypass / traffic leak bugs  
- Cryptography or log confidentiality failures  

Include: version, OS, reproduction steps, impact assessment, and whether a fix is proposed.

We aim to acknowledge within 7 days.

## Threat model (summary)

Trench Coat protects against **network observers** (ISP, local Wi-Fi, some upstream hops) when configured correctly. It does **not** magically defeat:

- Endpoint malware  
- Compromised hops you chose  
- Browser fingerprinting without a hardened browser  
- Global passive adversaries with unlimited correlation  
- Legal compulsion against you or your providers  

See `docs/security/HARDENING.md`, `docs/WHAT_THIS_DOES.md`, and `docs/dossiers/THREAT_MODEL.md`.
