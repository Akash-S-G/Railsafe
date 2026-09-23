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

def download_datasets(datasets, use_kaggle=True):
    for ds in datasets:
        script = ROOT / "datasets" / f"download_{ds}.sh"
        if script.exists():
            run(f"bash {script}", check=False)
        else:
            print(f"No script for {ds}")
    # Fallbacks for surface_faults if Mendeley 404: use Kaggle mirror
    surface_dir = ROOT / "datasets" / "track_surface_faults" / "Railway Track Surface Faults Dataset"
    if not surface_dir.exists() or len(list(surface_dir.glob("*/*.JPEG"))) < 5000:
        print("Surface faults missing (<5000), trying Kaggle mirror imenesabeur/test-xception...")
        run(f"kaggle datasets download -d imenesabeur/test-xception -p {ROOT}/datasets/track_surface_faults --unzip", check=False)
    # Kaggle Input mount: if user added dataset via UI, copy from /kaggle/input
    if Path("/kaggle/input").exists():
        for inp in Path("/kaggle/input").glob("*railway-component*"):
            print(f"Found Kaggle Input dataset: {inp}")
            import shutil
            dest = ROOT / "datasets" / "railsense"
            dest.mkdir(parents=True, exist_ok=True)
            # inp may contain data/ or direct component folders
            src_data = inp / "data" if (inp / "data").exists() else inp
            for comp in ["crossties","fasteners","fishplates","tracks"]:
                if (src_data / comp).exists():
                    run(f"cp -r {src_data/comp} {dest}/ 2>&1 | head", check=False)
                elif (inp / comp).exists():
                    run(f"cp -r {inp/comp} {dest}/ 2>&1 | head", check=False)
        for inp in Path("/kaggle/input").glob("*surface*"):
            print(f"Found Kaggle Input surface: {inp}")
        # also handle generic railsense input name variations
        for inp in Path("/kaggle/input").iterdir():
            if inp.is_dir() and any((inp / c).exists() for c in ["crossties","fasteners"]):
                print(f"Copying railsense from {inp} -> datasets/railsense")
                import shutil
                for c in ["crossties","fasteners","fishplates","tracks"]:
                    if (inp / c).exists():
                        run(f"cp -r {inp/c} {ROOT}/datasets/railsense/ 2>&1 | head", check=False)
                    if (inp / "data" / c).exists():
                        run(f"cp -r {inp/'data'/c} {ROOT}/datasets/railsense/ 2>&1 | head", check=False)

def build_manifest():
    run(f"{sys.executable} ml/dataset_tools/convert_to_manifest.py --datasets railsense surface_faults")
    run(f"{sys.executable} ml/dataset_tools/prepare_yolo.py")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", nargs="+", default=["railsense","surface_faults"])
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
