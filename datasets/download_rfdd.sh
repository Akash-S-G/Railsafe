#!/usr/bin/env bash
# RFDD — Railway Fastener Defect Dataset (MIT code, ScienceDB dataset)
# DOI: 10.57760/sciencedb.msdc.00071  CSTR:14923.11.sciencedb.msdc.00071
# Verified 2026-09-15: 1,350 imgs 2048x2021 (1050/200/100), >8,100 instances, 6 classes,
# HDF5 (train/val) + PNG (test), pixel masks+boxes, 8.24 GB, GH 23 commits MIT
# GH: https://github.com/NIM-NMDC/RFDD  ScienceDB: https://www.scidb.cn/detail?dataSetId=07e4f65e9ec346d180de7d37cb42bf44
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
DEST="$ROOT/rfdd"
mkdir -p "$DEST"
echo "=== RFDD (ScienceDB 10.57760/sciencedb.msdc.00071) ==="
echo "Size: 8.24 GB | 1,350 images 2048x2021 | 1050/200/100 split | MIT"
echo "Classes: Normal, Missing, Reversed (=Inverted), Displaced, Deformed, Broken (=Fractured)"

# Option 1: direct ScienceDB page (requires free registration, then download link)
echo ""
echo "[option 1] Recommended — browser download (free ScienceDB account):"
echo "  1) Visit https://www.scidb.cn/detail?dataSetId=07e4f65e9ec346d180de7d37cb42bf44"
echo "     or https://doi.org/10.57760/sciencedb.msdc.00071"
echo "  2) Log in (free) -> Download (1 file, 8.24 GB)"
echo "  3) Save to $DEST/ and extract (HDF5 for train/val, PNG for test)"

# Option 2: try direct CSTR resolver (may redirect)
CSTR_URL="https://cstr.cn/14923.11.sciencedb.msdc.00071"
echo ""
echo "[option 2] CSTR resolver: $CSTR_URL"

# Option 3: clone code (benchmarks + utils) — dataset itself not in GH raw (GH notice: full release upon acceptance)
echo ""
echo "[code] Cloning RFDD code for benchmarks ..."
if [ ! -d "$DEST/RFDD-code" ]; then
  git clone https://github.com/NIM-NMDC/RFDD.git "$DEST/RFDD-code"
else
  echo "  already cloned at $DEST/RFDD-code"
fi
echo "  Benchmarks: YOLOv9c 0.9668 mAP50 best, YOLO11m 0.7106 mAP50:95 best (test=100)"
echo "  Weights: https://aistudio.baidu.com/dataset/detail/364368/intro (Baidu login required)"

# Option 4: attempt curl to ScienceDB download endpoint (often requires auth token — will likely fail without login)
if command -v curl &>/dev/null; then
  echo ""
  echo "[try] Probing ScienceDB DOI redirect ..."
  curl -I -L -s "https://doi.org/10.57760/sciencedb.msdc.00071" | head -n 20 || true
fi

echo ""
echo "Expected after download & extract:"
echo "  $DEST/<hdf5_files_for_train_val>/  +  $DEST/<png_for_test>/  + masks/boxes"
echo "See docs/datasets/datasets.md Dataset C"
