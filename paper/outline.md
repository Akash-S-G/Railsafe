# IEEE Paper Outline — RailSafe (v1, 6-8 pages, 2-column)

> **Scope:** v1 only (Exp1-6 + ablation A-C). Exp7-9 + Dataset G moved to Future Work.

## Sections

1. **Abstract** (150w): YOLO11 + RailSense hybrid, component-centric, explainable risk; RFDD/Surface/RailSense datasets; no temporal claims.
2. **Introduction:** railway inspection gap (thousands of frames, single-image defect insufficient), risk prioritization need.
3. **Related Work:** RailSense (proxy AE), RFDD benchmark (YOLO/RT-DETR), YOLOv8+self-supervised, MDPI Sensors 2026 survey (data/generalization gaps).
4. **Datasets:** Table (7 datasets, locked DOIs/sizes/licenses); honest strategy — no longitudinal public dataset exists, so temporal gated.
5. **Method:** 5 layers (diagram): Component Detection (YOLO11m, per-dataset heads, grouped splits) → Anomaly (RailSense ResNet50 256×256×3, α·(1-SSIM)+L1, topk/ssim_map, mean+k·std) vs PatchCore/PaDiM → Fusion (KNOWN vs UNKNOWN_ABNORMALITY) → Severity S=w1D+w2A+w3G+w4C → Risk v1 R=w1S+… (0-100 LOW/MED/HIGH/CRITICAL, contributors).
6. **Experiments:** Exp1 RailSense repro (AUROC/AUPRC/recall@P≥0.90), Exp2 PatchCore/PaDiM, Exp3 YOLO vs RT-DETR (mAP50/50:95) + cross-dataset, Exp4 hybrid, Exp5 localization (IoU/pixel AUROC/AUPRO on RFDD masks), Exp6 severity, ablation A-C.
7. **Results:** Tables + PR curves + heatmaps + map screenshot.
8. **Limitations:** No public longitudinal dataset → no deterioration claim; v2 gated; domain shift.
9. **Conclusion & Future Work:** Temporal association (Aij), deterioration (β1), ranking (Precision@K/NDCG@K) once Dataset G collected.
10. **References:** Lock DOIs from docs/datasets/data-license.md BibTeX.

## Template

Use IEEE Conference LaTeX: `\documentclass[conference]{IEEEtran}`. Place figures: pipeline, heatmap triptych, map.
