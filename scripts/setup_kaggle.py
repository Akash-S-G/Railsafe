#!/usr/bin/env python3
"""
Kaggle / Colab setup: clone repo, install deps, download datasets via Kaggle API, build manifest.
Works identically on Kaggle Notebooks (Add Data -> GitHub) and Colab (!git clone).
Usage on Kaggle:
  !python scripts/setup_kaggle.py --datasets railsense surface_faults --kaggle-key $KAGGLE_KEY
On Colab:
  !git clone https://github.com/YOUR/RAILSAFE.git && cd RAILSAFE
  !python scripts/setup_kaggle.py
It detects Kaggle env via /kaggle/input and Colab via google.colab module.
"""
import argparse, os, subprocess, sys, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def run(cmd, check=True):
    print(f"$ {cmd}")
    r = subprocess.run(cmd, shell=True)
    if check and r.returncode!=0:
        print(f"Failed: {cmd}")
        sys.exit(r.returncode)
    return r

def setup_kaggle_api(key_json: str = None):
    # Kaggle API uses ~/.kaggle/kaggle.json or access_token (Kaggle 2.2.4)
    kaggle_dir = Path.home() / ".kaggle"
    kaggle_dir.mkdir(parents=True, exist_ok=True)
    if key_json and Path(key_json).exists():
        # user passed path to kaggle.json
        import shutil; shutil.copy(key_json, kaggle_dir / "kaggle.json")
        (kaggle_dir / "kaggle.json").chmod(0o600)
        print("Kaggle API configured from file")
    elif os.environ.get("KAGGLE_USERNAME") and os.environ.get("KAGGLE_KEY"):
        # Colab secrets
        data = {"username": os.environ["KAGGLE_USERNAME"], "key": os.environ["KAGGLE_KEY"]}
        (kaggle_dir / "kaggle.json").write_text(json.dumps(data))
        (kaggle_dir / "kaggle.json").chmod(0o600)
        print("Kaggle API configured from env vars")
    else:
        print("No Kaggle API key found — will try fallback (surface_faults mirror may still work if already cached)")

def install_deps(mode="kaggle"):
    # Kaggle already has torch+torchvision, but we pin ultralytics+anomalib for Phase 3
    print("Installing Python deps...")
    if mode=="kaggle":
        # Kaggle notebooks: pip install is safe (no PEP668)
        run(f"{sys.executable} -m pip install -q -r ml/requirements.txt")
    else:
        run(f"{sys.executable} -m pip install -q -r ml/requirements.txt --break-system-packages")
    # TF for RailSense Phase 1 (optional, heavy) — install only if requested
    # run(f"{sys.executable} -m pip install -q tensorflow==2.16.1")

def find_input_dir(predicate, min_matches=1, markers=None, depth=3):
    """Find a /kaggle/input dir matching predicate name OR containing marker subdirs."""
    inp_root = Path("/kaggle/input")
    if not inp_root.exists():
        return None
    for inp in sorted(inp_root.iterdir()):
        if not inp.is_dir():
            continue
        if predicate(inp.name.lower().replace("-", "_").replace("_", "_")):
            return inp
        # check marker subdirs up to depth
        if markers:
            for sub in [inp] + list(inp.rglob("*")):
                try:
                    if sub.is_dir() and any((sub / m).exists() for m in markers):
                        hits = sum(1 for m in markers if (sub / m).exists())
                        if hits >= min_matches:
                            return sub.parent if sub != inp else inp
                except (OSError, PermissionError):
                    continue
    return None

def copy_dir_tree(src: Path, dst: Path):
    import shutil
    dst.mkdir(parents=True, exist_ok=True)
    for p in src.rglob("*"):
        if p.is_file():
            out = dst / p.relative_to(src)
            out.parent.mkdir(parents=True, exist_ok=True)
            if not out.exists():
                shutil.copy2(p, out)

def copy_from_kaggle_input():
    """Copy user-added datasets from /kaggle/input mount (Add Data -> Kaggle Datasets UI)."""
    inp_root = Path("/kaggle/input")
    if not inp_root.exists():
        return

    # 1. railsense: any input with crossties/fasteners/fishplates/tracks
    rs = find_input_dir(lambda n: "railway" in n and "component" in n, markers=["crossties", "fasteners"])
    if rs is None:
        rs = find_input_dir(lambda n: False, markers=["crossties", "fasteners", "fishplates"], min_matches=2)
    if rs:
        print(f"[input] railsense found at {rs}")
        dest = ROOT / "datasets" / "railsense"
        dest.mkdir(parents=True, exist_ok=True)
        # data root may be rs itself, rs/data, or a nested folder
        src_data = None
        for cand in [rs, rs / "data"] + [d for d in rs.rglob("*") if d.is_dir() and (d / "crossties").exists()]:
            if (cand / "crossties").exists():
                src_data = cand
                break
        if src_data:
            for comp in ["crossties", "fasteners", "fishplates", "tracks"]:
                if (src_data / comp).exists() and not (dest / comp).exists():
                    copy_dir_tree(src_data / comp, dest / comp)
                    print(f"  copied {comp}")
        else:
            print("  warning: no component folders found in input")

    # 2. kaggle_multiclass: any input with All_non-defective/Fastener_defective/Rail_defective
    mc = find_input_dir(lambda n: "multiclass" in n, markers=["All_non-defective", "Fastener_defective", "Rail_defective"])
    if mc:
        print(f"[input] multiclass found at {mc}")
        dest = ROOT / "datasets" / "kaggle_multiclass"
        dest.mkdir(parents=True, exist_ok=True)
        src_data = None
        for cand in [mc] + [d for d in mc.rglob("*") if d.is_dir() and (d / "All_non-defective").exists()]:
            if (cand / "All_non-defective").exists():
                src_data = cand
                break
        if src_data:
            for cls in ["All_non-defective", "Fastener_defective", "Rail_defective"]:
                if (src_data / cls).exists() and not (dest / cls).exists():
                    copy_dir_tree(src_data / cls, dest / cls)
                    print(f"  copied {cls}")
        else:
            print("  warning: no class folders found in input")

    # 3. surface_faults: any input with the 7 class folders (Cracks/Flakings/...)
    surface_markers = ["Cracks", "Flakings", "Squats", "Grooves", "Joints", "Shellings", "Spallings"]
    sf = find_input_dir(lambda n: "surface" in n or "xception" in n, markers=surface_markers, min_matches=3)
    if sf:
        print(f"[input] surface faults found at {sf}")
        dest = ROOT / "datasets" / "track_surface_faults" / "Railway Track Surface Faults Dataset"
        dest.mkdir(parents=True, exist_ok=True)
        src_data = None
        for cand in [sf] + [d for d in sf.rglob("*") if d.is_dir() and (d / "Cracks").exists()]:
            if (cand / "Cracks").exists():
                src_data = cand
                break
        if src_data:
            for cls in surface_markers:
                if (src_data / cls).exists() and not (dest / cls).exists():
                    copy_dir_tree(src_data / cls, dest / cls)
                    print(f"  copied {cls}")
        else:
            print("  warning: no class folders found in input")
    else:
        print("[input] surface faults NOT in /kaggle/input — add 'imenesabeur/test-xception' via Add Input, or API download will run")

def download_datasets(datasets, use_kaggle=True):
    # FIRST: copy whatever the user added via Add Input UI (no API needed)
    copy_from_kaggle_input()
    for ds in datasets:
        script = ROOT / "datasets" / f"download_{ds}.sh"
        if script.exists():
            run(f"bash {script}", check=False)
        elif ds == "kaggle_multiclass":
            # public Kaggle multiclass supplement (3-class: Normal/Fastener_defective/Rail_defective)
            mc_dir = ROOT / "datasets" / "kaggle_multiclass" / "Raillway-Track-Multiclass-dataset"
            mc_flat = ROOT / "datasets" / "kaggle_multiclass"
            have_mc = any(len(list(d.rglob("*.jpg"))) >= 1000 for d in [mc_dir, mc_flat] if d.exists())
            if not have_mc:
                print("kaggle_multiclass missing (<1000), downloading salmaneunus/railwayfaultmulticlassdataset...")
                run(f"kaggle datasets download -d salmaneunus/railwayfaultmulticlassdataset -p {ROOT}/datasets/kaggle_multiclass --unzip", check=False)
        else:
            print(f"No script for {ds}")
    # Fallbacks for surface_faults if still missing (input copy + Mendeley 404): use Kaggle mirror API
    surface_dir = ROOT / "datasets" / "track_surface_faults" / "Railway Track Surface Faults Dataset"
    if not surface_dir.exists() or len(list(surface_dir.rglob("*.JPEG"))) < 5000:
        print("Surface faults missing (<5000), trying Kaggle mirror imenesabeur/test-xception...")
        run(f"kaggle datasets download -d imenesabeur/test-xception -p {ROOT}/datasets/track_surface_faults --unzip", check=False)

def build_manifest():
    run(f"{sys.executable} ml/dataset_tools/convert_to_manifest.py --datasets railsense surface_faults kaggle_multiclass")
    run(f"{sys.executable} ml/dataset_tools/prepare_yolo.py")                 # 7-class surface layout
    run(f"{sys.executable} ml/dataset_tools/prepare_yolo.py --task multiclass")  # 3-class multiclass layout

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", nargs="+", default=["railsense","surface_faults","kaggle_multiclass"])
    ap.add_argument("--kaggle-key", type=str, default=None, help="path to kaggle.json")
    ap.add_argument("--skip-install", action="store_true")
    ap.add_argument("--skip-download", action="store_true")
    args = ap.parse_args()
    if args.kaggle_key or os.environ.get("KAGGLE_KEY"):
        setup_kaggle_api(args.kaggle_key)
    if not args.skip_install:
        mode = "kaggle" if Path("/kaggle").exists() else "colab"
        install_deps(mode)
    if not args.skip_download:
        download_datasets(args.datasets)
    build_manifest()
    print("Setup done. Next: python scripts/train.py --task all")

if __name__ == "__main__":
    main()
