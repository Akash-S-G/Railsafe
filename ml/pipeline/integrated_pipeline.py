#!/usr/bin/env python3
"""
Phase 4-6 Integrated Pipeline: Full frame -> YOLO -> crop 256 -> RailSense anomaly + YOLO defect -> fusion -> severity -> risk
CPU-friendly, reuses existing envs (ultralytics + .venv-railsense TF optional).

Usage:
  python ml/pipeline/integrated_pipeline.py --image datasets/yolo_surface/test/Squats/xxx.JPEG
  python ml/pipeline/integrated_pipeline.py --image datasets/yolo_surface/test/Flakings/xxx.JPEG --chainage 124320 --track UP

Saves: experiments/results/pipeline/<image>.json with full Ct=[A,D,S,L,Q] + contributors
"""
import argparse, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from ml.severity.severity_engine import compute_severity
from ml.risk.risk_engine import compute_risk_v1

def run_pipeline(image: Path, chainage=124320, track="UP", line="LINE-01"):
    from ultralytics import YOLO
    # Load YOLO cls (surface) — for full-scene we mock bbox as whole image (no RFDD det yet)
    yolo_weights = ROOT / "experiments" / "results" / "best_surface_cls.pt"
    if not yolo_weights.exists():
        yolo_weights = ROOT / "runs" / "yolo" / "surface_classify" / "weights" / "best.pt"
    if not yolo_weights.exists():
        print(f"YOLO weights not found: {yolo_weights}")
        sys.exit(1)
    yolo = YOLO(str(yolo_weights))
    # YOLO defect prediction
    res = yolo.predict(str(image), verbose=False)[0]
    probs = res.probs
    defect_type = yolo.names[probs.top1]
    defect_conf = float(probs.top1conf)
    # Mock anomaly: RailSense would give 0.81 for unknown, here use 0.3-0.9 based on defect_conf
    # If defect is Squats/Cracks high severity, anomaly high; else moderate
    anomaly = 0.85 if defect_type in ["Cracks","Squats","Broken"] else 0.45 if defect_type in ["Flakings","Shellings"] else 0.25
    # Try real RailSense if available (TF)
    try:
        # lightweight: if TF available, run dummy railsense via hardlink data
        import tensorflow as tf  # noqa
        # For now mock, real would be: railsense.predict(crop 256)
        pass
    except: pass
    # Affected area mock: from defect type
    affected_area = {"Cracks":0.27,"Squats":0.31,"Flakings":0.18,"Shellings":0.22,"Spallings":0.15}.get(defect_type, 0.1)
    # Fusion logic per hybrid-fusion.md
    status = "KNOWN_DEFECT" if defect_conf >= 0.5 else ("UNKNOWN_ABNORMALITY" if anomaly >= 0.5 else "NORMAL")
    # Severity
    sev = compute_severity(anomaly, defect_type, affected_area, "rail")
    # Risk
    risk = compute_risk_v1(sev["severity"], 0.95, affected_area, location_factor=0.6)
    out = {
        "image": str(image),
        "component_type": "rail",
        "known_defect": {"type": defect_type, "confidence": round(defect_conf,3)},
        "anomaly": round(anomaly,3),
        "status": status,
        "bbox": [0,0,224,224],  # mock full-frame, real RFDD would have [x,y,w,h]
        "heatmap_path": None,
        "condition": {"A": anomaly, "D": defect_type, "S": sev["severity"], "L": chainage, "Q": sev["level"]},
        "severity": sev,
        "risk": risk,
        "asset_id": f"RAIL-{chainage}-{track}",
        "chainage_m": chainage, "track_id": track, "line_id": line,
    }
    out_dir = ROOT / "experiments" / "results" / "pipeline"
    out_dir.mkdir(parents=True, exist_ok=True)
    save = out_dir / f"{image.stem}.json"
    save.write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
    print(f"Saved -> {save}")
    return out

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", type=Path, required=True)
    ap.add_argument("--chainage", type=float, default=124320)
    ap.add_argument("--track", type=str, default="UP")
    ap.add_argument("--line", type=str, default="LINE-01")
    args = ap.parse_args()
    run_pipeline(args.image, args.chainage, args.track, args.line)
