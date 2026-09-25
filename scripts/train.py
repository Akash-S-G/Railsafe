#!/usr/bin/env python3
"""
Unified training entrypoint for Kaggle / Colab / Local.
Covers v1 pipeline: Phase 1 RailSense (TF) + Phase 3 YOLO classify (surface) + evaluate.
RFDD gated — skips gracefully if not present.

Usage:
  python scripts/train.py --task railsense           # Phase 1 only (requires TF)
  python scripts/train.py --task yolo --epochs 20 --model yolo11n.pt
  python scripts/train.py --task all --epochs 10     # both
  python scripts/train.py --task yolo --dry-run      # check data.yaml without training

Kaggle example (2 clicks):
  1) New Notebook -> Add Data -> GitHub -> YOUR/RAILSAFE
  2) !python scripts/setup_kaggle.py && python scripts/train.py --task yolo --epochs 5

Colab example:
  !git clone https://github.com/YOUR/RAILSAFE.git && cd RAILSAFE
  !python scripts/setup_kaggle.py
  !python scripts/train.py --task all --epochs 10
"""
import argparse, sys, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def run(cmd, check=True):
    print(f"\n$ {cmd}")
    r = subprocess.run(cmd, shell=True)
    if check and r.returncode!=0:
        print(f"Command failed: {cmd}")
        sys.exit(r.returncode)
    return r

def train_railsense(epochs=5, batch=16):
    # RailSense needs TF. If not installed, print instruction.
    try:
        import tensorflow
        print(f"TF {tensorflow.__version__} found")
    except ImportError:
        print("TensorFlow not installed. Run: pip install tensorflow==2.16.1")
        print("Skipping railsense training (dry-run mode).")
        return
    # Link data if needed
    rs_code = ROOT / "datasets" / "railsense" / "RailSense-code"
    data_link = rs_code / "data"
    if not data_link.exists():
        # symlink each component to avoid recursive copy
        data_link.mkdir(parents=True, exist_ok=True)
        for comp in ["crossties","fasteners","fishplates","tracks"]:
            src = ROOT / "datasets" / "railsense" / comp
            dst = data_link / comp
            if src.exists() and not dst.exists():
                dst.symlink_to(src.resolve())
                print(f"Linked {src} -> {dst}")
    # train fasteners only for speed (257 images)
    run(f"cd {rs_code} && python main.py both --epochs {epochs} --batch_size {batch} --run_name kaggle-fastener")

def train_yolo(epochs=10, model="yolo11n.pt", task="classify", dry_run=False, dataset="surface"):
    """dataset: surface (7-class) or multiclass (3-class Normal/Fastener_defective/Rail_defective)"""
    manifest = ROOT / "datasets" / "manifest.jsonl"
    if not manifest.exists():
        print("manifest.jsonl missing — running convert_to_manifest.py")
        run(f"{sys.executable} ml/dataset_tools/convert_to_manifest.py --datasets railsense surface_faults kaggle_multiclass")
    if dataset == "multiclass":
        data_yaml = ROOT / "datasets" / "multiclass_data.yaml"
        yolo_root = ROOT / "datasets" / "yolo_multiclass"
        run_name = "multiclass_cls"
        prep_args = "--task multiclass"
    else:
        data_yaml = ROOT / "datasets" / "surface_data.yaml"
        yolo_root = ROOT / "datasets" / "yolo_surface"
        run_name = "surface_classify"
        prep_args = ""
    if not data_yaml.exists() or not yolo_root.exists():
        run(f"{sys.executable} ml/dataset_tools/prepare_yolo.py {prep_args}".strip())
    if dry_run:
        print(f"Dry run OK: {data_yaml} exists, {yolo_root} ready")
        import json
        recs = [json.loads(l) for l in manifest.read_text().splitlines() if l.strip()]
        from collections import Counter
        print("Manifest:", Counter(r["dataset_id"] for r in recs))
        for split in ["train","val"]:
            p = yolo_root / split
            if p.exists():
                print(f"  {split}: {len(list(p.rglob('*.JPEG')))+len(list(p.rglob('*.jpg')))} images, classes={[d.name for d in p.iterdir() if d.is_dir()]}")
        return
    try:
        from ultralytics import YOLO
    except ImportError:
        print("ultralytics not installed. Install ml/requirements.txt")
        sys.exit(1)
    # Auto-switch to classification model if user passed detection weights
    if not model.endswith("-cls.pt"):
        cls_model = model.replace(".pt", "-cls.pt")
        print(f"Classification dataset detected — switching {model} -> {cls_model}")
        model = cls_model
    print(f"Training YOLO {model} for {epochs} epochs on {yolo_root} (classification, {dataset})")
    yolo = YOLO(model)
    yolo.train(data=str(yolo_root), epochs=epochs, imgsz=224, batch=16, project=str(ROOT/"runs"/"yolo"), name=run_name)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", choices=["railsense","yolo","multiclass","all"], default="yolo", help="what to train")
    ap.add_argument("--epochs", type=int, default=10)
    ap.add_argument("--model", type=str, default="yolo11n.pt", help="yolo model: yolo11n.pt (2.6M fast) or yolo11m.pt (20.1M best)")
    ap.add_argument("--dry-run", action="store_true", help="only check data, don't train")
    ap.add_argument("--batch", type=int, default=16)
    args = ap.parse_args()

    if args.task in ["railsense","all"]:
        train_railsense(epochs=min(args.epochs, 5) if args.task=="all" else args.epochs, batch=args.batch)
    if args.task in ["yolo","all"]:
        train_yolo(epochs=args.epochs, model=args.model, dry_run=args.dry_run, dataset="surface")
    if args.task in ["multiclass","all"]:
        train_yolo(epochs=args.epochs, model=args.model, dry_run=args.dry_run, dataset="multiclass")

    print("\nDone. Check runs/yolo/ and datasets/manifest.jsonl")
    print("Next: python ml/severity/severity_engine.py + ml/risk/risk_engine.py for severity/risk demo")

if __name__ == "__main__":
    main()
