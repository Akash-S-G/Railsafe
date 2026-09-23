#!/usr/bin/env python3
"""
Test model in experiments/results/best_surface_cls.pt (or runs/.../best.pt)
- Single image predict + full test/val eval
- Saves predictions to experiments/results/predictions/

Usage:
  python scripts/test_results_model.py --weights experiments/results/best_surface_cls.pt --split test
  python scripts/test_results_model.py --weights experiments/results/best_surface_cls.pt --image datasets/yolo_surface/test/Squats/xxx.JPEG
  python scripts/test_results_model.py --weights runs/yolo/surface_classify/weights/best.pt --split val

On Kaggle:
  !python scripts/test_results_model.py --weights experiments/results/best_surface_cls.pt --split test
"""
import argparse, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

def test_split(weights: Path, split="test"):
    from ultralytics import YOLO
    data_root = ROOT / "datasets" / "yolo_surface"
    results_dir = ROOT / "experiments" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    print(f"Testing {weights} on {split} ({data_root}/{split})")
    if not weights.exists():
        print(f"Weights not found: {weights}")
        sys.exit(1)
    if not (data_root / split).exists():
        print(f"Dataset split not found: {data_root/split} — run prepare_yolo.py first")
        sys.exit(1)
    model = YOLO(str(weights))
    # Classification val: data is folder, split is val/test
    metrics = model.val(data=str(data_root), split=split)
    out = {
        "weights": str(weights),
        "split": split,
        "top1": float(metrics.top1),
        "top5": float(metrics.top5),
    }
    # per-class try
    try:
        # metrics dict may contain per-class top1
        print(f"top1 {out['top1']:.4f} top5 {out['top5']:.4f}")
    except: pass
    save = results_dir / f"test_{split}_{weights.stem}.json"
    save.write_text(json.dumps(out, indent=2))
    print(f"Saved {save}")
    # also save predictions on 5 samples
    preds_dir = results_dir / f"predictions_{split}"
    preds_dir.mkdir(exist_ok=True)
    # run predict on 5 random test images
    import random
    samples = list((data_root / split).rglob("*.JPEG")) + list((data_root / split).rglob("*.jpeg")) + list((data_root / split).rglob("*.jpg"))
    random.seed(0)
    random.shuffle(samples)
    for p in samples[:5]:
        r = model.predict(str(p), verbose=False)
        # r[0].probs.top1, top5
        probs = r[0].probs
        pred = {
            "image": str(p.relative_to(ROOT)),
            "true_class": p.parent.name,
            "pred_class": model.names[probs.top1],
            "top1_conf": float(probs.top1conf),
            "top5": [model.names[i] for i in probs.top5],
        }
        print(f"{p.parent.name} -> {pred['pred_class']} ({pred['top1_conf']:.2f})")
        (preds_dir / f"{p.stem}.json").write_text(json.dumps(pred, indent=2))
    print(f"Predictions saved to {preds_dir}/ (*.json)")

def test_image(weights: Path, image: Path):
    from ultralytics import YOLO
    if not weights.exists():
        print(f"Weights not found: {weights}")
        sys.exit(1)
    if not image.exists():
        print(f"Image not found: {image}")
        sys.exit(1)
    model = YOLO(str(weights))
    results = model.predict(str(image), verbose=True)
    probs = results[0].probs
    print(f"Image: {image}")
    print(f"Pred: {model.names[probs.top1]} conf {probs.top1conf:.4f}")
    print(f"Top5: {[(model.names[i], float(probs.top5conf[j])) for j,i in enumerate(probs.top5)]}")
    # severity/risk demo with anomaly placeholder
    try:
        from ml.severity.severity_engine import compute_severity
        from ml.risk.risk_engine import compute_risk_v1
        # use top1 confidence as defect_score, anomaly 0.7 as example
        sev = compute_severity(0.7, model.names[probs.top1], 0.25, "rail")
        risk = compute_risk_v1(sev["severity"], 0.85, 0.25)
        print(f"Severity: {sev}")
        print(f"Risk: {risk}")
    except Exception as e:
        print(f"Severity demo skip: {e}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", type=Path, default=ROOT/"experiments"/"results"/"best_surface_cls.pt")
    ap.add_argument("--split", type=str, default=None, help="val or test for full split eval")
    ap.add_argument("--image", type=Path, default=None, help="single image path")
    args = ap.parse_args()
    if args.image:
        test_image(args.weights, args.image)
    elif args.split:
        test_split(args.weights, args.split)
    else:
        # default: test both val and test
        for s in ["val","test"]:
            test_split(args.weights, s)
