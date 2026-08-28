# Tauri desktop shell — Phase 4 Jazz for Ghosts

## Prerequisites

- Rust toolchain (`rustup`)
- Node.js 18+
- Platform bundlers (WiX / NSIS on Windows, etc.)

## Bootstrap

```bash
# from repo root
cd gui/tauri
npm create tauri-app@latest . -- --template vanilla  # if scaffolding empty
# or install CLI:
cargo install tauri-cli --version "^2"
```

Point the webview at the static nexus (`../web`) and run the Python control plane:

```bash
trench gui   # :8742
cargo tauri dev
```

## Package

```bash
cargo tauri build
# artifacts: MSI / DMG / AppImage under src-tauri/target/release/bundle
```

## Sidecar

Preferred production shape: ship `trench` as a Tauri sidecar binary (PyInstaller) that the UI spawns on loopback only.
