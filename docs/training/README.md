# Training on Kaggle / Colab — One-Click Guide

> Clone this repo and run `scripts/setup_kaggle.py + scripts/train.py` — works identically on Kaggle Notebooks and Google Colab. Uses the 2/3 primary datasets already verified (`railsense 858` + `surface_faults 5153`); RFDD 8.24GB is gated (manual ScienceDB).

## 1. Quick Start

### Kaggle (recommended, free T4 x2)

1. Create **New Notebook** → **Add Data** → **GitHub** → paste `https://github.com/YOUR/RAILSAFE`
2. In a code cell:

```python
!python scripts/setup_kaggle.py --datasets railsense surface_faults
!python scripts/train.py --task yolo --epochs 5 --model yolo11n.pt --dry-run  # check
!python scripts/train.py --task yolo --epochs 10 --model yolo11n.pt
```

Add Kaggle Secrets `KAGGLE_USERNAME` + `KAGGLE_KEY` (from kaggle.com/settings → Create New Token) if you want `railsense` via API — `surface_faults` mirror `imenesabeur/test-xception` works without keys.

### Colab (free T4)

```python
!git clone https://github.com/YOUR/RAILSAFE.git && cd RAILSAFE
!python scripts/setup_kaggle.py --datasets railsense surface_faults
!python scripts/train.py --task yolo --epochs 10 --model yolo11n.pt
```

## 2. What the Scripts Do

| Script | Purpose | Output |
|---|---|---|
| `scripts/setup_kaggle.py` | `pip install -r ml/requirements.txt` (torch cu121 + ultralytics), `bash datasets/download_*.sh` (Kaggle API + fallback mirror), `ml/dataset_tools/convert_to_manifest.py` | `datasets/manifest.jsonl` (grouped by `sequence_id`, no leakage) + `datasets/yolo_surface/{train,val,test}/` + `datasets/surface_data.yaml` |
| `ml/dataset_tools/convert_to_manifest.py` | Unified schema per `docs/datasets/schema.md:1` | `datasets/manifest.jsonl` (858 railsense + 5153 surface = 6011 records, splits `train 70% val 15% test 15%`, seeded 1337) |
| `ml/dataset_tools/prepare_yolo.py` | YOLO classify layout | `datasets/yolo_surface/` symlinks + `datasets/surface_data.yaml` (`nc 7`, names `Grooves..Squats`) |
| `scripts/train.py` | Unified entry: `railsense` (TF 2.16) / `yolo` (ultralytics) / `all` | `runs/yolo/surface_classify/weights/best.pt`, `output/heatmaps/` (railsense) |
| `notebooks/Train_on_Kaggle_Colab.ipynb` | 1-click notebook for both platforms | Copy-paste cells |

## 3. Training Tasks

```bash
# Surface head — 7-class rail surface defects (5153 imgs, works now)
python scripts/train.py --task yolo --epochs 10 --model yolo11n.pt    # 2.6M fast, ~10 min T4
python scripts/train.py --task yolo --epochs 100 --model yolo11m.pt   # 20.1M, best per ml/component_detection/config.yaml:3 (0.7106 mAP50:95)

# Multiclass head — 3-class Normal/Fastener_defective/Rail_defective (1185 imgs, ~2 min)
# Complementary head: adds the missing Normal class + fastener/rail defective (per-dataset heads, taxonomy.md)
python scripts/train.py --task multiclass --epochs 10 --model yolo11n.pt

# Both heads + dry-run checks
python scripts/train.py --task yolo --dry-run && python scripts/train.py --task multiclass --dry-run
python scripts/train.py --task all --epochs 10
```

### Datasets (3 public, one command)

| Dataset | Source | Size | Layout |
|---|---|---|---|
| RailSense | `kashtennyson/railway-component-dataset` (Kaggle API) | 858 imgs | `crossties/fasteners/fishplates/tracks × normal/damaged` |
| Surface Faults | Mendeley `10.17632/8hxtgyyxrw.2` → mirror `imenesabeur/test-xception` | 5153 imgs, 7 classes | class folders |
| Multiclass | `salmaneunus/railwayfaultmulticlassdataset` (public, auto) | 1185 imgs, 3 classes | `All_non-defective/Fastener_defective/Rail_defective` |

Splits (auto, no leakage): surface video-grouped (val = median video), multiclass IMG-dates grouped + instagram image-level stratified. Manifest: 7196 records, 13 groups verified.

## 4. Dataset Handling on Kaggle/Colab

- **RailSense** (`kashtennyson/railway-component-dataset` 5.99M): Downloaded via Kaggle API if `~/.kaggle/kaggle.json` present, else GH fallback `RailSense-code`.
- **Surface Faults** (`10.17632/8hxtgyyxrw.2`): Mendeley API returns 404 in headless — script falls back to Kaggle mirror `imenesabeur/test-xception` (303M, 5153 images verified).
- **RFDD** (`10.57760/sciencedb.msdc.00071` 8.24GB): `datasets/rfdd/` empty until you manually download from `https://www.scidb.cn/detail?dataSetId=07e4f65e9ec346d180de7d37cb42bf44` (free login). Training skips gracefully if absent; `ml/dataset_tools/convert_to_manifest.py` emits `rfdd: 0 records`.

## 5. Expected Outputs

```
datasets/manifest.jsonl  # 6011 lines, no leakage (checked per docs/research/leakage.md:60)
datasets/yolo_surface/train/Cracks/*.JPEG  # etc.
runs/yolo/surface_classify/weights/best.pt
runs/yolo/surface_classify/results.csv
output/heatmaps/*_triptych.png  # railsense only
```

Severity/risk demo (no training):

```bash
python -c "from ml.severity.severity_engine import compute_severity; print(compute_severity(0.81,'Cracks',0.27,'rail'))"
python -c "from ml.risk.risk_engine import compute_risk_v1; print(compute_risk_v1(0.68,0.85,0.27))"
```

## 6. Local Training (same commands)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r ml/requirements.txt
bash datasets/download_railsense.sh && bash datasets/download_surface_faults.sh
python ml/dataset_tools/convert_to_manifest.py
python ml/dataset_tools/prepare_yolo.py
python scripts/train.py --task yolo --epochs 10
```

## 7. Troubleshooting

- **Kaggle API 404**: Add Secrets `KAGGLE_USERNAME`/`KAGGLE_KEY`, or use mirror (auto).
- **TF vs Torch conflict**: RailSense uses `tensorflow>=2.10`, YOLO uses `torch`. Keep separate: `pip install -r ml/requirements.txt` for YOLO, `pip install tensorflow==2.16.1` only if running `railsense`.
- **Disk (Kaggle 20GB)**: RFDD 8.24GB exceeds Kaggle limit — skip it (`--datasets railsense surface_faults`).
- **YOLO OOM**: Use `yolo11n.pt` + `batch 8` on T4.

See `docs/REQUIREMENTS_LOCK.md` for locked versions and `docs/research/phases.md` for 14-phase order.
