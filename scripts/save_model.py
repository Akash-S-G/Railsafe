#!/usr/bin/env python3
"""
Save/export best model to experiments/results and ensure evals are in respective folders.
Usage: python scripts/save_model.py
Copies runs/yolo/surface_classify/weights/best.pt -> experiments/results/best.pt
and generates README with metrics.
"""
from pathlib import Path
import shutil, json

ROOT = Path(__file__).resolve().parents[1]
src = ROOT / "runs" / "yolo" / "surface_classify" / "weights" / "best.pt"
dst_dir = ROOT / "experiments" / "results"
dst_dir.mkdir(parents=True, exist_ok=True)
dst = dst_dir / "best_surface_cls.pt"
if src.exists():
    shutil.copy2(src, dst)
    print(f"Saved model {src} -> {dst} ({dst.stat().st_size/1e6:.2f} MB)")
else:
    print(f"Model not found: {src} (train first)")
# also check eval files
for p in [dst_dir / "eval_surface_val.json", dst_dir / "eval_surface_test.json", ROOT / "runs" / "yolo" / "surface_classify" / "metrics_val.json"]:
    print(f"{'✅' if p.exists() else '❌'} {p} {'exists' if p.exists() else 'missing — run scripts/evaluate.py'}")
