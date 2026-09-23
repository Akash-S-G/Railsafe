# Development Phases (14 Phases)

```mermaid
gantt
    title RailSafe Phases
    dateFormat  YYYY-MM-DD
    section Phase 0-2
    0 Research & Data Audit       :a1, 2026-09-15, 14d
    1 Reproduce RailSense         :a2, after a1, 7d
    2 Dataset Normalization       :a3, after a2, 10d
    section Phase 3-6
    3 Component Detector          :a4, after a3, 14d
    4 RailSense Integration       :a5, after a4, 7d
    5 Known Defect Detector       :a6, after a5, 14d
    6 Evidence Fusion             :a7, after a6, 7d
    section Phase 7-9
    7 Condition & Severity        :a8, after a7, 7d
    8 Asset Registry              :a9, after a8, 10d
    9 Risk Engine (v1 complete)   :a10, after a9, 10d
    section Phase 10-13 (Gated)
    10 Temporal Collection        :a11, after a10, 30d
    11 Temporal Association       :a12, after a11, 14d
    12 Deterioration              :a13, after a12, 14d
    13 Temporal Risk              :a14, after a13, 14d
    section Phase 14
    14 Dashboard & Report         :a15, after a3, 30d
```

| Phase | Name | Deliverable | Gated? |
|---|---|---|---|
| 0 | Research/Data Audit | `datasets.md`, `taxonomy.md`, `research_questions.md`, `data_license.md`, inventory | No |
| 1 | Reproduce RailSense | `python main.py both` baseline + W&B report | No |
| 2 | Dataset Normalization | Unified schema + `manifest.jsonl` + grouped splits | No |
| 3 | Component Detector | YOLO training + `mAP` vs RT-DETR (Exp 3) | No |
| 4 | RailSense Integration | `Full frame → detector → crop → RailSense → heatmap` pipeline | No |
| 5 | Known Defect Detector | Per-dataset heads (RFDD, Surface) | No |
| 6 | Evidence Fusion | Hybrid record + Exp 4 | No |
| 7 | Condition & Severity | `severity_engine.py` + Exp 6 | No |
| 8 | Asset Registry | PostGIS schema + `component_id` + GPS/chainage | No |
| 9 | Risk Engine | `risk_engine.py` + explainability + **v1 complete** | No |
| 10 | Temporal Collection | Dataset G (`asset_id + timestamp + location`) | **Yes** |
| 11 | Temporal Association | `association.py` + Exp 7 | **Yes** |
| 12 | Deterioration | `deterioration.py` linear/EMA before LSTM | **Yes** |
| 13 | Temporal Risk | `R_current` vs `R_current+deterioration` + Exp 9 | **Yes** |
| 14 | Dashboard | Map + Detail + Queue + report/presentation (parallel from Phase 2) | No |

## Recommended Order

```text
1→2→3→4→5→6→7→8→9  (v1 sequential, do not skip)
10 in parallel with 3-9 where possible (partner outreach)
11→12→13 after 10
14 continuous
```

- Do not start with LSTM (Phase 12): linear first.
- Dashboard (Phase 14) can start wireframes early, full data binding after Phase 9.
