#!/usr/bin/env python3
"""
Publish processed RailSafe dataset to Kaggle as a PRIVATE dataset (API, not git).
Packages yolo layouts (symlinks resolved to real copies) + manifests -> kaggle-uploadable folder.

One-time upload, then attach to any notebook via Add Data -> Your Datasets.
Images never touch git — this uses the Kaggle API only.

Usage:
  python scripts/publish_dataset_kaggle.py --package --slug YOUR-KAGGLE-USERNAME/railsafe-processed
  python scripts/publish_dataset_kaggle.py --package-only              # build folder, no upload
  python scripts/publish_dataset_kaggle.py --version -m "retrain msg"  # update existing
"""
import argparse, json, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "datasets" / "kaggle_upload_pkg"

SOURCES = [
    ("yolo_surface", ROOT / "datasets" / "yolo_surface"),
    ("yolo_multiclass", ROOT / "datasets" / "yolo_multiclass"),
    ("surface_data.yaml", ROOT / "datasets" / "surface_data.yaml"),
    ("multiclass_data.yaml", ROOT / "datasets" / "multiclass_data.yaml"),
]

def resolve_into(src: Path, dst: Path):
    """Copy symlinks as real files (Kaggle upload needs real bytes)."""
    if src.is_dir():
        dst.mkdir(parents=True, exist_ok=True)
        for p in src.rglob("*"):
            if p.is_file():
                real = p.resolve()
                out = dst / p.relative_to(src)
                out.parent.mkdir(parents=True, exist_ok=True)
                if not out.exists():
                    shutil.copy2(real, out)
    elif src.is_file():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src.resolve(), dst)

def package():
    if PKG.exists():
        shutil.rmtree(PKG)
    PKG.mkdir(parents=True, exist_ok=True)
    total = 0
    for name, src in SOURCES:
        if not src.exists():
            print(f"skip (missing): {name}")
            continue
        resolve_into(src, PKG / name)
        if src.is_dir():
            n = sum(1 for _ in (PKG / name).rglob("*") if _.is_file())
            print(f"packaged {name}: {n} files")
            total += n
        else:
            print(f"packaged {name}")
            total += 1
    # manifests (small, trackable in git too but included for completeness)
    for m in ["manifest.jsonl"]:
        p = ROOT / "datasets" / m
        if p.exists():
            shutil.copy2(p, PKG / m)
            print(f"packaged {m}")
    # metadata
    meta = {
        "title": "RailSafe Processed Dataset",
        "id": "",
        "licenses": [{"name": "CC0-1.0"}],
    }
    (PKG / "dataset-metadata.json").write_text(json.dumps(meta, indent=2))
    size = sum(f.stat().st_size for f in PKG.rglob("*") if f.is_file())
    print(f"Package ready: {PKG} ({total} files, {size/1e6:.0f} MB)")
    print(f"Next: python scripts/publish_dataset_kaggle.py --slug YOUR-USERNAME/railsafe-processed")
    return PKG

def upload(slug: str):
    meta_path = PKG / "dataset-metadata.json"
    meta = json.loads(meta_path.read_text())
    meta["id"] = slug
    meta_path.write_text(json.dumps(meta, indent=2))
    # create or version
    r = subprocess.run(f"kaggle datasets create -p {PKG}", shell=True)
    if r.returncode != 0:
        print("create failed — dataset may exist, trying version update...")
        msg = "update"
        subprocess.run(f"kaggle datasets version -p {PKG} -m '{msg}'", shell=True)
    print(f"Upload done (private by default). Attach in notebook: Add Data -> Your Datasets -> {slug.split('/')[-1]}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--package", action="store_true", help="build package folder")
    ap.add_argument("--package-only", action="store_true", help="build without upload")
    ap.add_argument("--version", action="store_true", help="update existing dataset version")
    ap.add_argument("--slug", type=str, default="", help="YOUR-KAGGLE-USERNAME/railsafe-processed")
    args = ap.parse_args()
    if args.package or args.package_only or args.version:
        package()
    if args.package_only:
        return
    if args.version:
        subprocess.run(f"kaggle datasets version -p {PKG} -m 'update'", shell=True)
        return
    if args.slug:
        upload(args.slug)
    else:
        print("Nothing to do — use --package-only, or --slug USER/railsafe-processed to upload")

if __name__ == "__main__":
    main()
