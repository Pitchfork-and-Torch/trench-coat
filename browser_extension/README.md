# Fingerprint companion (optional)

Separate trust domain from the Trench Coat engine.

- Popup reads local `/api/status`. It says Cloaked only when `running` is true and hops are not dead or degraded. Pending, stale, fail-closed, and a listening port with no owner stay not cloaked.
- Sets the Chromium proxy only after that, at `socks5://127.0.0.1:<listen port>` (default 1080).
- Minimal `navigator.webdriver` scrub (not a full fingerprint suite)

Load unpacked in Chrome: `chrome://extensions` → Developer mode → Load unpacked → this folder.

**High-risk work:** use Tor Browser, not this extension alone.
