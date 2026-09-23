"""
Phase 2: Unified manifest generator for Kaggle/Colab/local.
Converts heterogeneous sources -> datasets/manifest.jsonl per docs/datasets/schema.md:1
Handles: railsense (crop-level anomaly), surface_faults (image-level 7 classes), rfdd (optional, bbox+mask)
Grouping: surface_faults grouped by video prefix (7.MOV_...), railsense by component folder.
Usage:
  python ml/dataset_tools/convert_to_manifest.py --datasets railsense surface_faults [--output datasets/manifest.jsonl]
  python ml/dataset_tools/convert_to_manifest.py --check # leakage check only
"""
import argparse, json, os, re
from pathlib import Path
from collections import defaultdict
import random

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "datasets" / "manifest.jsonl"

SURFACE_CLASSES = ["Grooves","Joints","Cracks","Flakings","Shellings","Spallings","Squats"]
SURFACE_MAP = {c.lower(): c for c in SURFACE_CLASSES}  # folder names may vary

def parse_surface_sequence(filename: str):
    # 7.MOV_20201228114152_10038.JPEG -> 7.MOV_20201228114152
    m = re.match(r"(.+_\d+)_\d+\.", filename)
    return m.group(1) if m else filename.split("_")[0]

def convert_railsense(root: Path):
    base = root / "datasets" / "railsense"
    records = []
    if not base.exists():
        return records
    for component in ["crossties","fasteners","fishplates","tracks"]:
        comp_type = {"crossties":"sleeper","fasteners":"fastener","fishplates":"fishplate","tracks":"rail"}[component]
        for split_name in ["normal","damaged"]:
            folder = base / component / split_name
            if not folder.exists(): continue
            for p in folder.glob("*.jpg"):
                records.append({
                    "image_id": f"railsense_{component}_{p.stem}",
                    "dataset_id": "railsense",
                    "component_type": comp_type,
                    "defect_type": None if split_name=="normal" else split_name,  # keeps null for normal per schema:4
                    "bbox": None,
                    "mask_path": None,
                    "polyline": None,
                    "source": str(p.relative_to(ROOT)),
                    "sequence_id": f"railsense_{component}",  # group by component to avoid leakage across comps
                    "inspection_id": None,
                    "asset_id": None,
                    "timestamp": None,
                    "latitude": None,
                    "longitude": None,
                    "chainage_m": None,
                    "track_id": None,
                    "line_id": None,
                    "anomaly_score": None,
                    "severity": None,
                    "split": None,  # assigned later
                })
    return records

def convert_surface(root: Path):
    base = root / "datasets" / "track_surface_faults"
    # handle both nested and flat layouts
    search_roots = []
    if (base / "Railway Track Surface Faults Dataset").exists():
        search_roots.append(base / "Railway Track Surface Faults Dataset")
    if base.exists():
        search_roots.append(base)
    records = []
    seen = set()
    for sr in search_roots:
        for cls_folder in sr.iterdir():
            if not cls_folder.is_dir(): continue
            cls_name = cls_folder.name
            # normalize class name
            norm = cls_name.strip()
            # try to map: Cracks -> Cracks, etc.
            if norm.lower() not in [c.lower() for c in SURFACE_CLASSES]:
                continue
            canonical = next(c for c in SURFACE_CLASSES if c.lower()==norm.lower())
            for p in cls_folder.glob("*.JPEG"):
                if str(p) in seen: continue
                seen.add(str(p))
                if p.name.startswith("."): continue
                seq = parse_surface_sequence(p.name)
                records.append({
                    "image_id": f"surface_{p.stem}",
                    "dataset_id": "surface_faults",
                    "component_type": "rail",
                    "defect_type": canonical,
                    "bbox": None,  # image-level label only
                    "mask_path": None,
                    "polyline": None,
                    "source": str(p.relative_to(ROOT)),
                    "sequence_id": seq,
                    "inspection_id": None,
                    "asset_id": None,
                    "timestamp": None,
                    "latitude": None,
                    "longitude": None,
                    "chainage_m": None,
                    "track_id": None,
                    "line_id": None,
                    "anomaly_score": None,
                    "severity": None,
                    "split": None,
                })
            for p in cls_folder.glob("*.JPG"):
                if str(p) in seen: continue
                seen.add(str(p))
                seq = parse_surface_sequence(p.name)
                records.append({
                    "image_id": f"surface_{p.stem}",
                    "dataset_id": "surface_faults",
                    "component_type": "rail",
                    "defect_type": canonical,
                    "bbox": None,
                    "mask_path": None,
                    "polyline": None,
                    "source": str(p.relative_to(ROOT)),
                    "sequence_id": seq,
                    "inspection_id": None,
                    "asset_id": None,
                    "timestamp": None,
                    "latitude": None,
                    "longitude": None,
                    "chainage_m": None,
                    "track_id": None,
                    "line_id": None,
                    "anomaly_score": None,
                    "severity": None,
                    "split": None,
                })
            for p in cls_folder.glob("*.jpg"):
                if str(p) in seen: continue
                seen.add(str(p))
                seq = parse_surface_sequence(p.name)
                records.append({
                    "image_id": f"surface_{p.stem}",
                    "dataset_id": "surface_faults",
                    "component_type": "rail",
                    "defect_type": canonical,
                    "bbox": None,
                    "mask_path": None,
                    "polyline": None,
                    "source": str(p.relative_to(ROOT)),
                    "sequence_id": seq,
                    "inspection_id": None,
                    "asset_id": None,
                    "timestamp": None,
                    "latitude": None,
                    "longitude": None,
                    "chainage_m": None,
                    "track_id": None,
                    "line_id": None,
                    "anomaly_score": None,
                    "severity": None,
                    "split": None,
                })
    return records

def convert_rfdd(root: Path):
    # RFDD requires ScienceDB download (8.24GB). If not present, skip gracefully for Kaggle/Colab.
    base = root / "datasets" / "rfdd"
    records = []
    if not base.exists() or not any(base.glob("*.h5")):
        return records
    # Placeholder: RFDD HDF5 parsing would go here per docs/datasets/datasets.md:5
    # For now emit stub to keep manifest valid
    return records

def assign_grouped_splits(records, seed=1337, train_ratio=0.7, val_ratio=0.15):
    # Group by (dataset_id, sequence_id) to prevent leakage per docs/research/leakage.md:60
    # Per-dataset stratified: each dataset split independently to ensure val/test coverage
    from collections import defaultdict
    # bucket by dataset_id
    by_ds = defaultdict(list)
    for r in records:
        by_ds[r["dataset_id"]].append(r)
    for ds, ds_recs in by_ds.items():
        groups = defaultdict(list)
        for r in ds_recs:
            key = (r["dataset_id"], r["sequence_id"] or r["image_id"])
            groups[key].append(r)
        keys = list(groups.keys())
        rnd = random.Random(seed + hash(ds) % 1000)
        rnd.shuffle(keys)
        n = len(keys)
        # ensure at least 1 val group if n>=3
        n_train = max(1, int(n * train_ratio)) if n>=3 else int(n * train_ratio)
        n_val = max(1, int(n * val_ratio)) if n>=3 else int(n * val_ratio)
        # adjust if rounding leaves 0 test
        if n_train + n_val >= n:
            n_val = max(0, n - n_train - 1)
        # edge: tiny groups (railsense 4 groups) -> ensure val+test
        if ds=="railsense" and n==4:
            n_train, n_val = 2, 1  # 2 train, 1 val, 1 test
        if ds=="surface_faults" and n>=10:
            # ensure val has at least 1 video (~10% of data)
            if n_val <1: n_val=1
        split_map = {}
        for i, k in enumerate(keys):
            if i < n_train: split_map[k] = "train"
            elif i < n_train + n_val: split_map[k] = "val"
            else: split_map[k] = "test"
        for r in ds_recs:
            k = (r["dataset_id"], r["sequence_id"] or r["image_id"])
            r["split"] = split_map[k]
    return records

def check_leakage(manifest_path: Path):
    recs = [json.loads(l) for l in manifest_path.read_text().splitlines() if l.strip()]
    groups = defaultdict(set)
    for r in recs:
        key = (r["dataset_id"], r["sequence_id"] or r["image_id"])
        groups[key].add(r["split"])
    leaked = {k:v for k,v in groups.items() if len(v)>1}
    if leaked:
        print(f"LEAKAGE DETECTED: {len(leaked)} groups span splits")
        for k,v in list(leaked.items())[:5]:
            print(k, v)
        return False
    print(f"OK: {len(recs)} records, {len(groups)} groups, no leakage (grouped by sequence_id per leakage.md)")
    return True

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", nargs="+", default=["railsense","surface_faults","rfdd"], help="which converters to run")
    ap.add_argument("--output", type=Path, default=DEFAULT_MANIFEST)
    ap.add_argument("--seed", type=int, default=1337)
    ap.add_argument("--check", action="store_true", help="only check leakage on existing manifest")
    args = ap.parse_args()
    if args.check:
        ok = check_leakage(args.output)
        exit(0 if ok else 1)
    all_records = []
    if "railsense" in args.datasets:
        r = convert_railsense(ROOT)
        print(f"railsense: {len(r)} images (expected 858)")
        all_records.extend(r)
    if "surface_faults" in args.datasets:
        r = convert_surface(ROOT)
        print(f"surface_faults: {len(r)} images (expected 5153)")
        all_records.extend(r)
    if "rfdd" in args.datasets:
        r = convert_rfdd(ROOT)
        print(f"rfdd: {len(r)} records (0 if not downloaded yet)")
        all_records.extend(r)
    if not all_records:
        print("No records found. Check datasets/ layout per datasets/README.md:40")
        return
    all_records = assign_grouped_splits(all_records, seed=args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output,"w") as f:
        for r in all_records:
            f.write(json.dumps(r)+"\n")
    print(f"Wrote {len(all_records)} records -> {args.output}")
    # summary per split
    from collections import Counter
    cnt = Counter(r["split"] for r in all_records)
    print(f"Splits: {dict(cnt)}")
    # per dataset
    for ds in set(r["dataset_id"] for r in all_records):
        c = Counter(r["split"] for r in all_records if r["dataset_id"]==ds)
        print(f"  {ds}: {dict(c)}")
    check_leakage(args.output)

if __name__ == "__main__":
    main()
