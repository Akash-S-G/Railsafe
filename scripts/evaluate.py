#!/usr/bin/env python3
"""
Evaluation: runs YOLO val/test, saves metrics to experiments/results + runs/yolo/.
Usage:
  python scripts/evaluate.py --weights runs/yolo/surface_classify/weights/best.pt --split val
  python scripts/evaluate.py --weights runs/yolo/surface_classify/weights/best.pt --split test
"""
import argparse, json
from pathlib import Path
import subprocess, sys

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "experiments" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def eval_yolo(weights: Path, split="val"):
    from ultralytics import YOLO
    data_root = ROOT / "datasets" / "yolo_surface"
    print(f"Evaluating {weights} on {split} ({data_root}/{split})")
    model = YOLO(str(weights))
    # YOLO val uses data param; for classification it expects folder
    # Use data=str(data_root) and split param via model.val()
    metrics = model.val(data=str(data_root), split=split)
    # metrics is dict-like; save
    out = {
        "weights": str(weights),
        "split": split,
        "top1": float(getattr(metrics, 'top1', 0) or metrics.get('top1',0) if isinstance(metrics, dict) else 0),
        "top5": float(getattr(metrics, 'top5', 0) or metrics.get('top5',0) if isinstance(metrics, dict) else 0),
    }
    # fallback: ultralytics returns Results object with attributes
    try:
        out["top1"] = float(metrics.top1)
        out["top5"] = float(metrics.top5)
    except: pass
    try:
        # also try box metrics if detection
        out["fitness"] = float(metrics.fitness) if hasattr(metrics, 'fitness') else None
    except: pass
    # save
    save_path = RESULTS_DIR / f"eval_surface_{split}.json"
    # also save to runs dir
    runs_save = weights.parent.parent / f"metrics_{split}.json"
    for p in [save_path, runs_save]:
        p.write_text(json.dumps(out, indent=2))
        print(f"Saved {p}: {out}")
    # also run severity/risk demo and save
    try:
        from ml.severity.severity_engine import compute_severity
        from ml.risk.risk_engine import compute_risk_v1
        demo = {
            "severity_example": compute_severity(0.81, "Cracks", 0.27, "rail"),
            "risk_example": compute_risk_v1(0.68, 0.85, 0.27),
        }
        (RESULTS_DIR / "severity_risk_demo.json").write_text(json.dumps(demo, indent=2))
        print(f"Severity/Risk demo saved to {RESULTS_DIR/'severity_risk_demo.json'}")
    except Exception as e:
        print(f"Severity demo skip: {e}")
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", type=Path, default=ROOT/"runs"/"yolo"/"surface_classify"/"weights"/"best.pt")
    ap.add_argument("--split", choices=["val","test"], default="val")
    args = ap.parse_args()
    if not args.weights.exists():
        # try last.pt
        alt = args.weights.parent / "last.pt"
        if alt.exists():
            args.weights = alt
        else:
            print(f"Weights not found: {args.weights}")
            sys.exit(1)
    eval_yolo(args.weights, args.split)

if __name__ == "__main__":
    main()
