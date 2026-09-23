#!/usr/bin/env bash
# Rail-DB — Rail-Detection (MIT, 96★, ACM MM 2022)
# 7,432 pairs, 9 scenes, polylines, row-based Rail-Net 92.77% @312 FPS
# Verified 2026-09-15: GH https://github.com/Sampson-Lee/Rail-Detection  form-gated download
# Optional for RailSafe v1 — scaffold code works without data
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
DEST="$ROOT/raildb"
mkdir -p "$DEST"
echo "=== Rail-DB (Sampson-Lee/Rail-Detection, ACM MM 2022) ==="
echo "Size: 7,432 image/annotation pairs, 9 scenes, polyline annotations, MIT"
echo "Download is form-gated (Google Form -> email link):"
echo "  https://docs.google.com/forms/d/e/1FAIpQLSemB6S2Oai4oC_mI2jxYb-KVfOVflmqY1scxEUtV24_-YP0aQ/viewform"
echo ""
echo "[steps]"
echo "  1) Fill the form with your email"
echo "  2) Receive email with download link (check spam)"
echo "  3) Download ZIP and unzip into $DEST/"
echo ""
echo "[code] Cloning Rail-Detection for reference (no data needed) ..."
if [ ! -d "$DEST/Rail-Detection-code" ]; then
  git clone https://github.com/Sampson-Lee/Rail-Detection.git "$DEST/Rail-Detection-code"
else
  echo "  already cloned at $DEST/Rail-Detection-code"
fi
echo "  Pretrained models: https://drive.google.com/file/d/1vd8rbUEkeoHpGP4QR0dc6LrS2un2FAF3/view?usp=sharing"
echo "  Launch training: bash launch_training.sh (after configs/raildb.py)"
echo ""
echo "Expected after download:"
echo "  $DEST/<images>/ + $DEST/<annotations_polylines>/  (9 scene subfolders)"
echo "See docs/datasets/datasets.md Dataset E (optional)"
