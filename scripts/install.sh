#!/usr/bin/env bash
# Trench Coat — Unix installer
set -euo pipefail

echo ""
echo "  TRENCH COAT :: INSTALL"
echo "  THE SHADOWS ARE YOUR ALLY"
echo ""

REPO="${TRENCH_COAT_REPO:-https://github.com/Pitchfork-and-Torch/trench-coat.git}"
TARGET="${TRENCH_COAT_HOME:-$HOME/trench-coat}"

if ! command -v python3 >/dev/null; then
  echo "python3 required" >&2
  exit 1
fi

if [[ ! -d "$TARGET" ]]; then
  if command -v git >/dev/null; then
    git clone "$REPO" "$TARGET"
  else
    echo "git required to clone, or set TARGET to an existing checkout" >&2
    exit 1
  fi
fi

cd "$TARGET"
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip
if [[ "${TRENCH_DEV:-}" == "1" ]]; then
  pip install -e ".[dev]"
else
  pip install -e .
fi

echo ""
echo "  Install complete."
echo "  source $TARGET/.venv/bin/activate"
echo "  trench first-run --accept-legal"
echo "  trench doctor"
echo "  trench up --accept-legal --wait-tor 60"
echo ""
