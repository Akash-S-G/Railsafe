#!/usr/bin/env bash
# Railway Track Surface Faults — Mendeley Data (CC BY 4.0, Public)
# DOI: 10.17632/8hxtgyyxrw.2  Version 2 (2022-01-06)  5,153 images  7 classes
# Source verified 2026-09-15: https://data.mendeley.com/datasets/8hxtgyyxrw/2  CC BY 4.0
# Note: Direct download requires accepting Mendeley terms on the page; this script
# tries the public data API endpoint. If it fails, download manually via browser.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
DEST="$ROOT/track_surface_faults"
mkdir -p "$DEST"
DOI="10.17632/8hxtgyyxrw.2"
echo "=== Railway Track Surface Faults (Mendeley, DOI $DOI) ==="
echo "License: CC BY 4.0  |  Classes: Grooves, Joints, Cracks, Flakings, Shellings, Spallings, Squats"

# Try Mendeley Data API (requires no auth for public dataset files listing)
# Fallback: instruct manual download
API_URL="https://data.mendeley.com/public/datasets/8hxtgyyxrw/files"
echo "[info] Trying $API_URL ..."
if command -v curl &>/dev/null; then
  if curl -fsSL "$API_URL" -o "$DEST/mendeley_files.json"; then
    echo "[ok] File listing saved to $DEST/mendeley_files.json"
    cat "$DEST/mendeley_files.json" | head -n 50
    echo "..."
    echo "[next] Download individual ZIPs from the URLs in that JSON, or download 'Download All' from the Mendeley page:"
    echo "  https://data.mendeley.com/datasets/8hxtgyyxrw/2"
  else
    echo "[warn] API fetch failed (Mendeley may require browser session). Manual download:"
    echo "  1) Visit https://data.mendeley.com/datasets/8hxtgyyxrw/2"
    echo "  2) Click 'Download All' (ZIP)"
    echo "  3) Unzip into $DEST/"
  fi
else
  echo "[warn] curl not found — manual download required:"
  echo "  https://data.mendeley.com/datasets/8hxtgyyxrw/2"
fi

# Also provide the Data in Brief paper for class reference
echo "Paper: https://doi.org/10.1016/j.dib.2024.110050"
echo "Expected after unzip: $DEST/*.jpg + annotations (check ZIP structure)"
echo "See docs/datasets/datasets.md Dataset B"
