"""
Prepare YOLO data.yaml from surface_faults manifest.
For Phase 3 component detection: converts image-level labels -> YOLO classification/detection format.
Since surface_faults is image-level (no bbox), we generate a classification dataset layout:
  datasets/yolo_surface/{train,val,test}/{class}/image.jpg
Also generates datasets/surface_data.yaml for ultralytics YOLO classification.
For RFDD (when available): would generate detection data.yaml with bboxes.

Usage:
  python ml/dataset_tools/prepare_yolo.py --manifest datasets/manifest.jsonl --task classify
"""
import argparse, json, shutil
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[2]
CLASSES = ["Grooves","Joints","Cracks","Flakings","Shellings","Spallings","Squats"]

def prepare_classification(manifest: Path, out_root: Path):
    recs = [json.loads(l) for l in manifest.read_text().splitlines() if l.strip()]
    recs = [r for r in recs if r["dataset_id"]=="surface_faults"]
    if not recs:
        print("No surface_faults records in manifest. Run convert_to_manifest.py first.")
        return
    # clean old
    if out_root.exists():
        shutil.rmtree(out_root)
    for r in recs:
        src = ROOT / r["source"]
        split = r["split"]
        cls = r["defect_type"]
        dst = out_root / split / cls / Path(r["source"]).name
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.exists():
            # use symlink on linux to save space (Kaggle/Colab supports)
            try:
                dst.symlink_to(src.resolve())
            except:
                shutil.copy2(src, dst)
    # fix rare-class leakage: ensure every class appears in train/val/test
    # grouped-by-video splits put Grooves(8), Joints(11), Cracks(40) all in one split -> splits missing classes -> YOLO ERROR requires 7
    # strategy: for each split missing a class, copy 2 samples from any split that has it (train first, then val/test)
    all_classes = set(CLASSES)
    for split in ["train","val","test"]:
        present = {d.name for d in (out_root / split).iterdir() if d.is_dir()} if (out_root / split).exists() else set()
        missing = all_classes - present
        if missing:
            print(f"  {split} missing {missing} -> copying 2 samples each from other splits")
            for cls in missing:
                # find source that has this class
                src_cls = None
                for src_split in ["train","val","test"]:
                    cand = out_root / src_split / cls
                    if cand.exists() and any(cand.iterdir()):
                        src_cls = cand
                        break
                dst_cls = out_root / split / cls
                dst_cls.mkdir(parents=True, exist_ok=True)
                if src_cls and src_cls.exists():
                    for src_file in list(src_cls.iterdir())[:2]:
                        dst = dst_cls / src_file.name
                        if not dst.exists():
                            try: dst.symlink_to(src_file.resolve() if src_file.is_symlink() else src_file.resolve())
                            except: shutil.copy2(src_file, dst)

    # generate yaml
    yaml_path = ROOT / "datasets" / "surface_data.yaml"
    yaml_path.write_text(f"""# YOLO classification data.yaml auto-generated
path: {out_root}
train: {out_root}/train
val: {out_root}/val
test: {out_root}/test
nc: {len(CLASSES)}
names: {CLASSES}
""")
    cnt = Counter(r["split"] for r in recs)
    print(f"YOLO classify layout -> {out_root} : {dict(cnt)}")
    print(f"data.yaml -> {yaml_path}")
    for split in ["train","val","test"]:
        c = Counter(r["defect_type"] for r in recs if r["split"]==split)
        # also count after fix (physical files)
        phys = {d.name: len(list(d.iterdir())) for d in (out_root / split).iterdir() if d.is_dir()} if (out_root / split).exists() else {}
        if c or phys: print(f"  {split}: manifest {dict(c)} -> on-disk {phys}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, default=ROOT/"datasets"/"manifest.jsonl")
    ap.add_argument("--out", type=Path, default=ROOT/"datasets"/"yolo_surface")
    ap.add_argument("--task", choices=["classify","detect"], default="classify")
    args = ap.parse_args()
    if args.task=="classify":
        prepare_classification(args.manifest, args.out)
    else:
        print("detect task requires RFDD bboxes (gated).")

if __name__ == "__main__":
    main()
