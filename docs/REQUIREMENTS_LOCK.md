# Requirements Lock — RailSafe (Verified 2026-09-15)

> **Status: LOCKED** — All versions, sizes, licenses, and claim boundaries verified via live web fetch on 2026-09-15. Any change requires explicit version bump.

## 1. Locked Sources (Do Not Change Without Re-verification)

| Requirement | Locked Value | Verification | Change Requires |
|---|---|---|---|
| RailSense model | ResNet50 `conv4_block6_out` frozen → 1×1 LATENT_DIM → transposed-conv 256×256×3; loss `α·(1-SSIM)+(1-α)L1`; scoring `global_mse/topk/ssim_map`; threshold `mean+k·std` | GH fetch 51 commits MIT | — |
| RailSense CLI | `python main.py train/evaluate/predict/both --wandb` | GH README | — |
| Surface Faults | Mendeley DOI `10.17632/8hxtgyyxrw.2` v2 2022-01-06, **5,153 images**, 7 classes, **120 FPS EKEN-H9R, 14" FOV**, CC BY 4.0 | Mendeley page | — |
| RFDD | **1,350 imgs 2048×2021**, **1050/200/100** split, **>8,100 instances**, 6 classes Normal/Missing/Reversed/Displaced/Deformed/Broken, **HDF5+PNG**, masks+boxes, **6 principles Geometry/Optics/Boundary/Noise/Texture/Hierarchy**, MIT, ScienceDB `10.57760/sciencedb.msdc.00071` v1 2025-12-26 8.24GB | GH + scidb.cn | — |
| RFDD benchmarks (test=100) | RT-DETR 0.9038/0.5996, YOLOv8m 0.9665/0.6517, YOLOv9c **0.9668**/0.6796, YOLOv10m 0.9439/0.6730, **YOLO11m 0.9614/0.7106 best 50:95** | GH README | — |
| Rail-5k | **Restricted — email application only**, BY-NC-ND 4.0, ~5000 (0.03mm/px), 1100 annotated 13 types, DOI `10.5281/zenodo.4872619` → `4872772` current | Zenodo + arXiv 2106.14366 | Email grant before use |
| Rail-DB | **7,432 pairs**, 9 scenes, polylines, **92.77% @312 FPS lightweight**, MIT, form download | GH + ACM MM paper | — |
| Subgrade | **661 records**, 8 types (settlement 233, uplift 88, frost 254…), 239 districts, WGS84, CC BY, figshare `10.6084/m9.figshare.24086016` | Nature page | — |
| Detector | **YOLO11 Sep 2024 primary** (39.5-54.7 mAP), RT-DETR comparison, AGPL-3.0/Enterprise | Ultralytics Roadmap + GH 60k★ | — |
| Anomaly compare | **PaDiM (ICPR 2020, AUROC 0.945/0.968)** vs **PatchCore (CVPR 2022, AUROC 0.979-0.99)** via **anomalib** | arXiv + anomalib tables | — |
| Licenses | RailSense MIT, Surface CC BY 4.0, RFDD MIT, Rail-DB MIT, Subgrade CC BY, Rail-5k restricted BY-NC-ND 4.0 | GH LICENSE + Mendeley + Zenodo | — |

## 2. Locked Scope — What We Build

### v1 (supported NOW — no gate)

```
Full frame → YOLO11 (RFDD+Surface per-dataset heads, grouped splits) → crop → RailSense (component-specific) + PatchCore/PaDiM (Exp2)
→ Hybrid fusion (KNOWN_DEFECT vs UNKNOWN_ABNORMALITY) → bbox + heatmap (anomaly localization map) → Ct=[A,D,S,L,Q] → S=w1D+w2A+w3G+w4C (prototype weights)
→ asset_id via GPS/chainage/track+line (PostGIS) → R=w1S+w2C+w3A+w4L (R∈[0,100] LOW/MED/HIGH/CRITICAL support thresholds) + contributors
→ Dashboard (Overview + Map + Detail + Queue) + FastAPI + W&B
```

### v2 (GATED — requires Dataset G)

```
Dataset G (asset_id + timestamp + image + location + condition, ≥4 obs/asset, same physical asset re-observed)
→ Association Aij = wgGij+wvVij+wsSij (GPS/chainage + DINOv2/ResNet cosine + Hungarian) → deterioration C(t)=β0+β1t → EMA/Kalman → LSTM only if n sufficient
→ Risk R=w1S+w2D+w3C+w4A+w5L → Exp7/8/9 gated
```

### v3 (OUT OF SCOPE)

Failure forecasting — requires outcome data (inspection→maintenance→failure). Do not claim.

## 3. Locked Decisions (Ask User Before Changing)

| # | Decision | Locked | Alternative | Ask User |
|---|---|---|---|---|
| 1 | Use ScienceDB DOI for RFDD download, not GH raw | Yes | GH raw (incomplete) | No — locked |
| 2 | Treat Rail-5k as external validation only, not primary | Yes | Primary | If access granted, elevate |
| 3 | PostGIS from start (not SQLite prototype) | Yes | SQLite | Confirm infra |
| 4 | YOLO11m primary (best mAP50:95 0.7106) | Yes | YOLOv8m fallback | Confirm GPU budget |
| 5 | Component-specific anomaly models (H2) | Yes | Generic | No — locked per H2 |
| 6 | Threshold mean+k·std on val normal, not fixed 0.5 | Yes | Fixed | No — locked |
| 7 | Heatmap = "anomaly localization map" until RFDD mask validation | Yes | Claim segmentation | No — locked |
| 8 | Weights = prototype, not safety thresholds | Yes | Claim safety | No — locked |
| 9 | Do not fake temporal (no synthetic crack, no cross-asset Δ) | Yes | Synthetic | No — locked |
| 10 | Grouped splits (sequence_id/asset_id) required | Yes | Random | No — locked |

## 4. Locked Technology Stack

```text
Python 3.10+ / PyTorch / ultralytics>=8.3 / anomalib>=1.0 / opencv-python / timm / scikit-learn / albumentations
FastAPI + SQLAlchemy + PostgreSQL 14+ + PostGIS 3+ + Redis(optional)
React 18 + Vite 5 + Tailwind 3 + Leaflet 1.9 (default) + Recharts
W&B
Node 20+
```

## 5. Locked Metrics (Per Module)

```
Detection: mAP@50, mAP@50:95, Precision/Recall/F1
Anomaly: AUROC/AUPRC/F1 + recall@precision≥0.90 (RailSense)
Localization: IoU/pixel AUROC/AUPRO (RFDD masks)
Severity: MAE/RMSE/weighted F1
Association[gated]: Precision/Recall/F1/ID switches
Deterioration[gated]: MAE/RMSE/R²/Spearman
Ranking[gated]: Precision@K/Recall@K/NDCG@K
```

## 6. Locked File Locations (Repo Scaffold)

```text
datasets/{railsense,track_surface_faults,rfdd,temporal}
ml/{component_detection,defect_detection,anomaly_detection/{railsense,patchcore,padim},severity,temporal,risk}
backend/{api,models,schemas,services,database}
frontend/
experiments/{baselines,ablations,temporal,results}
docs/architecture/ (9), docs/datasets/ (4), docs/research/ (7), docs/literature/matrix.md
```

## 7. Final Lock — User Decisions (2026-09-15, Build Mode)

| # | Item | User Decision | Locked Action |
|---|---|---|---|
| 1 | Compute | **Cloud GPU** | Train **YOLO11m primary** (20.1M, best RFDD mAP50:95 0.7106) with batch 16 on Cloud GPU; fallback YOLO11n (2.6M) for ablations/edge. All training scripts default to Cloud GPU (CUDA 12). |
| 2 | Kaggle | **Can get Kaggle datasets** | Use **Kaggle API** for RailSense (`kashtennyson/railway-component-dataset`) as primary; GH clone as fallback. Script checks `~/.kaggle/kaggle.json`. |
| 3 | Public downloads | **Public downloads OK** | Mendeley Surface Faults (CC BY 4.0, direct ZIP) + RFDD ScienceDB (direct DOI `10.57760/sciencedb.msdc.00071` → scidb.cn; 8.24 GB HDF5+PNG) are **public** — provide direct curl/wget scripts. No account wall beyond free ScienceDB/Mendeley registration. |
| 4 | Rail-5k / Rail-DB | **Defer restricted** | Rail-5k = **SKIP** (restricted BY-NC-ND 4.0, email gate, 0 downloads). Rail-DB = **form-gated** (Google Form) — mark optional, scaffold code without data initially. Do not block v1. |
| 5 | Dataset G / Temporal | **No public longitudinal dataset exists** (confirmed) | **v1-only for build + IEEE paper.** v2 temporal stays **GATED / Future Work** in paper. Architecture retains `temporal/` module as stub with interfaces (`association.py`, `deterioration.py`) but no claims. Paper states limitation explicitly (per MDPI Sensors 906 data-availability challenge). |
| 6 | Deployment | **Local demo** | **FastAPI + PostgreSQL 14 + PostGIS 3 locally** (Docker Compose). Frontend `npm run dev` locally. YOLO under **AGPL-3.0** (open, non-commercial) — fine for IEEE/local. No Enterprise license needed. |
| 7 | Report | **IEEE double-column** | Lock to **IEEE Conference template** (2-column, 6-8 pages). Structure: Introduction → Related Work → Datasets → Method (5 layers) → Experiments (Exp1-6 + ablation A-C) → Results → Limitations (temporal gated) → Conclusion. Exp7-9 moved to Future Work. |

> **Status: FINAL LOCK** — Phase 0 audit proceeds to download scripts for public datasets only. Restricted datasets (Rail-5k) excluded from v1.

## 8. Audit Trail

- 2026-09-15 13:59: Initial verification — all web fetches succeeded; GH/Mendeley/ScienceDB/Zenodo/Nature pages confirm values above
- 2026-09-15 14:30: Final Lock — user confirmed Cloud GPU, Kaggle OK, public downloads OK, no public Dataset G, local demo + IEEE paper. Earlier provisional values corrected: RFDD 6 principles locked to Hierarchy (not Texture & Occlusion), Surface Faults FPS/FOV locked, Rail-5k restricted status locked, RailSense ResNet50 truncated point + loss + scoring locked
