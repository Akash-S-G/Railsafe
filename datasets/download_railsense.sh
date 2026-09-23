#!/usr/bin/env bash
# RailSense — Railway Component Dataset (Kaggle + GitHub fallback)
# Verified 2026-09-15: GH MIT (51 commits), Kaggle kashtennyson/railway-component-dataset
# License: MIT (code), images are controlled proxy — check Kaggle terms before redistributing
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
DEST="$ROOT/railsense"
mkdir -p "$DEST"
echo "=== RailSense download ==="
if command -v kaggle &>/dev/null && [ -f "$HOME/.kaggle/kaggle.json" ]; then
  echo "[kaggle] downloading kashtennyson/railway-component-dataset ..."
  kaggle datasets download -d kashtennyson/railway-component-dataset -p "$DEST" --unzip
  echo "[kaggle] done -> $DEST"
elif command -v kaggle &>/dev/null; then
  echo "[kaggle] found but ~/.kaggle/kaggle.json missing. Get API token from https://www.kaggle.com/settings -> Create New Token"
  echo "Falling back to GitHub clone (code only, not images) ..."
  git clone https://github.com/kashtennyson/RailSense.git "$DEST/RailSense-code" || echo "already cloned"
  echo "Place Kaggle data under $DEST/{crossties,fasteners,fishplates,tracks}/{normal,damaged}/"
else
  echo "[kaggle] not installed. Installing via pip ..."
  echo "  pip install kaggle"
  echo "Then re-run this script."
  echo "Cloning code for reference ..."
  git clone https://github.com/kashtennyson/RailSense.git "$DEST/RailSense-code" || echo "already cloned"
fi
echo "Expected layout after download:"
echo "  $DEST/crossties/normal/  $DEST/crossties/damaged/"
echo "  $DEST/fasteners/normal/ $DEST/fasteners/damaged/"
echo "  $DEST/fishplates/normal/ $DEST/fishplates/damaged/"
echo "  $DEST/tracks/normal/    $DEST/tracks/damaged/"
echo "See docs/datasets/datasets.md Dataset A"
