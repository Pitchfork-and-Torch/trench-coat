#!/usr/bin/env bash
# Start system tor if available, else print guidance for Tor Browser SOCKS (9150).
set -euo pipefail

if ss -ltn 2>/dev/null | grep -qE ':9050|:9150' || netstat -ltn 2>/dev/null | grep -qE ':9050|:9150'; then
  echo "Tor SOCKS already listening (9050 or 9150)."
  exit 0
fi

if command -v tor >/dev/null 2>&1; then
  echo "Starting system tor..."
  if command -v systemctl >/dev/null 2>&1; then
    sudo systemctl start tor || tor &
  else
    tor &
  fi
  sleep 3
  echo "Tor started — expect socks5://127.0.0.1:9050"
  exit 0
fi

cat <<'EOF'
No system tor found.
Install Tor:
  - Debian/Ubuntu: sudo apt install tor
  - Fedora: sudo dnf install tor
  - macOS: brew install tor
  - Or install Tor Browser (SOCKS often on 9150)

Then: trench tor status && trench up --accept-legal
EOF
exit 1
