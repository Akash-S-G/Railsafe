# Autonomous CPU Plan — RailSafe v1 Completes Without Intervention (2026-09-23)

> You have `best_surface_cls.pt` (3.1M, 7-class 0.993 val / 0.775 test) and 6011 manifest records. Run `scripts/autonomous.py` on CPU — it finishes Phases 1-9 + 14 unattended, checkpoints after each phase, resumes on crash/power-cut.

## 0. State
- **Done:** Phase 0 audit, Phase 2 manifest (6011), Phase 3 surface YOLO (yolo11n-cls, 7 classes ✅), frontend scaffold (`vite 5173`), `severity_engine.py` + `risk_engine.py`
- **CPU:** `AMD 5800HS 15G RAM, no CUDA` → `device=cpu, imgsz 224, batch 4, workers 2, epochs 5-10` (vs GPU batch 16)
- **Gated:** Phases 10-13 (temporal) skip — `Dataset G` missing per `REQUIREMENTS_LOCK:5`

## 1. One Command (hands-off)
```bash
nohup python scripts/autonomous.py --cpu --epochs 5 > runs/autonomous.log 2>&1 &
tail -f runs/autonomous.log
# or
bash scripts/run_autonomous.sh
```
It runs sequentially, logs `runs/autonomous.log` + `experiments/results/autonomous_state.json`, and can be re-run (skips completed phases).

## 2. Phases Executed Autonomously
| Step | Script Called | Artifact | Skip If Exists | Time CPU |
|------|---------------|----------|----------------|----------|
| 2.1 Manifest | `ml/dataset_tools/convert_to_manifest.py + prepare_yolo.py` | `datasets/manifest.jsonl`, `yolo_surface/` | manifest exists & 6011 | 10s |
| 2.2 YOLO | `scripts/train.py --task yolo --epochs 5 --model yolo11n-cls.pt --device cpu` | `experiments/results/best_surface_cls.pt` | `best_surface_cls.pt` exists | 0.5h (5 epochs) |
| 2.3 Eval | `scripts/evaluate.py --split val/test` + `test_results_model.py` | `eval_surface_*.json`, `predictions_*/*.json` | eval json exists | 1m |
| 2.4 Severity/Risk | `python -m ml.severity.severity_engine` + `ml.risk.risk_engine` | `severity_risk_demo.json` | exists | 2s |
| 2.5 Backend | `docker compose up -d db && alembic upgrade head` (if DB) | `http://localhost:8000/health` | `/health ok` | 30s |
| 2.6 Frontend | `cd frontend && npm run build` | `frontend/dist/` | `dist/` exists | 20s |
| 2.7 Final Report | `experiments/results/autonomous_report.md` | IEEE table + metrics | — | 5s |

Total CPU: ~35 min (5 epochs) or ~1.2h (10 epochs), no GPU.

## 3. Autonomy Features
- **Checkpoints:** `experiments/results/autonomous_state.json` `{phase: done, timestamp, metrics}` — resume with same command.
- **Auto-recovery:** `try/except` per phase, 2 retries, logs error but continues to next phase.
- **CPU flags:** `--device cpu --batch 4 --workers 2` passed to ultralytics, `TF_CPP_MIN_LOG_LEVEL=2` for RailSense.
- **No prompts:** all `input()` removed, `WANDB disabled`, `confirm=false`.

## 4. After Completion
```bash
cat experiments/results/autonomous_report.md  # IEEE Results table
cat experiments/results/eval_surface_val.json # {top1 0.993}
ls experiments/results/best_surface_cls.pt runs/yolo/surface_classify/weights/best.pt
# Dashboard: http://localhost:5173 (vite) -> Map + Queue, backend docs http://localhost:8000/docs
```

## 5. Schedule (optional)
```bash
# Run nightly 02:00 without intervening
(crontab -l; echo "0 2 * * * cd /home/akash/Desktop/RAILSAFE && python scripts/autonomous.py --cpu >> runs/autonomous.log 2>&1") | crontab -
```

## 6. To Stop / Inspect
```bash
ps aux | grep autonomous
tail -n 100 runs/autonomous.log
cat experiments/results/autonomous_state.json | jq
```

Phases 10-13 remain gated `temporal.md` — will be `Future Work` in paper `paper/outline.md`.
