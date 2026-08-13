# Windows WFP / full-tunnel notes

Full transparent redirect needs a signed WFP callout or a userspace divert driver.
MVP soft path: WinINET SOCKS via `trench route soft`.

Hard path (future):
- WFP ALE_AUTH_CONNECT filter allowing only Tor + Trench entry
- Always ship disable script before enable
- Never install permanent blocks without operator confirmation
