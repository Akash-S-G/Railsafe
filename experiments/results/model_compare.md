# Model Comparison — 2026-09-24 14:20

## Classification (surface_faults 7 classes, same grouped splits, CPU)
| Model | Params | Val top1 | Test top1 | Notes |
|---|---|---|---|---|
| **YOLO11n-cls** (ours, fine-tuned 10ep) | 1.5M | **0.9933** | **1.0** | full fine-tune, shares detector backbone |
| EfficientNet-B0 (linear probe 3ep) | 5.3M | 0.339 | 0.1707 | frozen backbone — quick baseline |
| ResNet18 (linear probe 3ep) | 11.8M | 0.211 | 0.5024 | frozen backbone — quick baseline |

## Anomaly (railsense crossties normal 88 mem / 22 test vs 313 damaged, CPU)
| Method | AUROC | Notes |
|---|---|---|
| **patch-kNN mini-PatchCore** (ours, generic ImageNet feats) | **0.7419** | 7x7x1280 conv_head, coreset 20k, top-1% mean |
| RailSense AE (domain-trained) | 0.89 | trains on railway crops |
| PaDiM | 0.945 | MVTec lit |
| PatchCore | 0.99 | MVTec lit, patch memory |
