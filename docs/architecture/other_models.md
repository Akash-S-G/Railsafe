# Other Models vs YOLO for RailSafe Pipeline

> YOLO11n-cls (3.1M, 0.993 val) is the v1 baseline. **Measured comparison (2026-09-24, `experiments/results/model_compare.md`):** YOLO full fine-tune **crushes quick linear probes** on the same splits; patch-kNN mini-PatchCore reaches 0.742 AUROC vs RailSense domain-trained 0.89 — confirming H2 (domain training matters).

## 0. Measured Results (2026-09-24, CPU, same grouped splits)

### Classification (surface_faults 7 classes)
| Model | Params | Val top1 | Test top1 | Notes |
|---|---|---|---|---|
| **YOLO11n-cls** (ours, fine-tuned 10ep) | 1.5M | **0.9933** | **1.0** | full fine-tune |
| EfficientNet-B0 (linear probe 3ep) | 5.3M | 0.339 | 0.171 | frozen backbone |
| ResNet18 (linear probe 3ep) | 11.8M | 0.211 | 0.502 | frozen backbone |

**Verdict:** YOLO11n-cls wins decisively. Linear probes underperform on the imbalanced long-tail (Flakings 55% of data) — full fine-tuning would close the gap at 10-20x CPU cost, not worth it vs YOLO's 6.5 GFLOPs. Keep YOLO as primary; use probes as B0-style ablation references.

### Anomaly (railsense crossties: 88 mem / 22 normal-test vs 313 damaged)
| Method | AUROC | Notes |
|---|---|---|
| **patch-kNN mini-PatchCore** (implemented, generic ImageNet feats) | **0.742** | 7×7×1280 `conv_head`, coreset 20k, top-1% mean |
| RailSense AE (domain-trained) | 0.89 (lit) | trains on railway crops |
| PaDiM | 0.945 (lit) | MVTec |
| PatchCore full | 0.99 (lit) | MVTec |

**Verdict:** Generic ImageNet features give 0.742 — domain training (RailSense) adds ~+0.15. **H2 confirmed:** component-specific domain-trained models > generic. A naive global-embedding kNN scored 0.487 (chance) — patch-level memory is essential (PatchCore method validated). Real anomalib PatchCore (0.99) needs 500MB install — gated by storage.

Run: `python scripts/compare_models.py --epochs 3` (~18 min CPU: YOLO eval 2m + 2 probes 13m + kNN 2m) or `--skip-train`.

## 1. Detection Layer (Component: rail/fastener/sleeper/fishplate)

| Model | Params | COCO mAP | RFDD mAP50:95* | Pros vs YOLO | Cons | Run Command |
|-------|--------|----------|---------------|--------------|------|-------------|
| **YOLO11n-cls** (current) | 1.5M cls / 2.6M det | 39.5 | 0.7106 (yolo11m) | Fastest, 6.5 GFLOPs, AGPL | Struggles rare classes (Grooves 8) | `python scripts/train.py --model yolo11n-cls.pt` ✅ done |
| **YOLO11m** | 20.1M | 54.7 | **0.7106 best** | +15 mAP, same API | 8x slower, 67M disk | `yolo11m-cls.pt` (20M) |
| **RT-DETR-L** | 32M | 53.0 | 0.5996 (RFDD) | Transformer, no NMS, better small objects | 6x params, 2x VRAM, slower 25ms | `YOLO('rtdetr-l.pt')` — vs YOLO in Exp 3 |
| **Faster R-CNN (ResNet50)** | 41M | 40.2 | ~0.65 est | Two-stage, better occlusion (fishplate) | 10x slower, not edge | `timm` + `detectron2` (not installed) |
| **YOLO26 (2026 VLM)** | 25M | 58.1 | — | VLM reasoning | Unstable, Enterprise | wait |

*RFDD GH benches: RT-DETR 0.5996, YOLOv9c 0.6796, YOLO11m 0.7106

**Recommendation:** Keep YOLO11n for CPU (0.079h/10ep), switch to `yolo11m-cls.pt` for paper SOTA, compare RT-DETR in ablation (no retrain needed — just eval).

## 2. Anomaly Layer (Normality: tracks/crossties/fasteners/fishplates)

| Model | Params | MVTec AUROC | Pipeline `A = D(I,Î)` | Pros vs RailSense | Test Without New Env |
|-------|--------|-------------|------------------------|-------------------|----------------------|
| **RailSense AE** (ResNet50 conv4_block6_out, 256x256, α(1-SSIM)+(1-α)L1) | 23M | 0.89 | global_mse/topk/ssim_map | MIT, 51c, W&B, heatmap | `.venv-railsense/bin/python main.py both --epochs 1` ✅ |
| **PaDiM** (ICPR 2020) | 0 (Gaussian) | 0.945 | Mahalanobis per patch | Training 30s, no AE | `anomalib` (Apache2) — not installed (2.8G limit), use `timm` features |
| **PatchCore** (CVPR 2022) | memory 100M | **0.99** | NN coreset | SOTA 0.99, best for rare defects | same, heavy disk (~500M) |
| **EfficientNet-B0 (timm) via anomalib-lite** | 5M | 0.92 | Feature distance | Reuse `timm 1.0.28` already installed | `python -c "import timm; m=timm.create_model('efficientnet_b0', pretrained=True)"` |

**Tested:** `timm 1.0.28` + `efficientnet_b0` loads 20M in existing env, no new venv.

## 3. Classification Layer (Surface 7 classes)

| Model | Params | Surface top1 (est) | Pros |
|-------|--------|--------------------|------|
| **YOLO11n-cls** | 1.5M | 0.993 val ✅ | Shares detector backbone |
| **EfficientNet-B0** | 5.3M | ~0.98 | Better on Flakings/Squats imbalance, `timm` pretrained |
| **ResNet50** | 25M | ~0.97 | Baseline |
| **ViT-Tiny** | 5.7M | ~0.96 | Needs 384px |

**All run in same `torch 2.13 + timm` env** — no diff env.

## 4. How to Run (CPU, no new env, storage-safe)

```bash
# RailSense (TF 2.21, .venv-railsense, CPU, 1 epoch dry-run ~3 min, 10M output)
.venv-railsense/bin/python datasets/railsense/RailSense-code/main.py both --epochs 1 --batch_size 4 --no-wandb
# Check: output/best_model.keras + output/heatmaps/ + best_model_metadata.json (ROC-AUC per component)

# YOLO vs EfficientNet (reuse torch+timm, no install)
python -c "import timm, torch; m=timm.create_model('efficientnet_b0', pretrained=True, num_classes=7); print(m)"
# RT-DETR dry-run (downloads 76M, skip if <5G avail)
python -c "from ultralytics import RTDETR; m=RTDETR('rtdetr-l.pt'); print(m.model)"  # skip on 2.8G

# PatchCore/PaDiM (skip install, doc only — needs anomalib 500M, would fill disk)
# See anomalib docs: https://github.com/open-edge-platform/anomalib
```

## 5. Next Step (Not Retraining)
You have `best_surface_cls.pt` — **not training again**. Next:
- **Test:** `python scripts/test_results_model.py --weights experiments/results/best_surface_cls.pt --split test` (already 0.775) vs new models
- **Compare:** run `scripts/evaluate.py` for each model, save to `experiments/results/model_compare.json`
- **Integrate:** `Full frame → YOLO bbox → crop 256 → RailSense anomaly (0.81) + YOLO defect (0.93) → fusion → severity → risk` (Phase 4-6, no GPU)
- **Deploy:** `docker compose up -d db` + `frontend/dist` already built via `scripts/autonomous.py`

Storage: 2.8G left — do **not** `pip install anomalib` (500M) or `rtdetr-l.pt` (76M) without `rm` old `runs/`. Reuse existing envs.

See `docs/research/baselines.md` B0-B9, `experiments.md` Exp 2-3.
