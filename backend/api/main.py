import json, shutil, sys, uuid
from pathlib import Path
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parents[2]
PIPELINE_DIR = ROOT / "experiments" / "results" / "pipeline"
UPLOAD_DIR = ROOT / "experiments" / "results" / "uploads"

app = FastAPI(title="RailSafe API", version="0.1.0 - v1 (no temporal)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok", "version": "v1", "temporal": "gated"}

@app.get("/")
def root():
    return {"name": "RailSafe", "docs": "/docs", "health": "/health"}

_yolo = None

def get_yolo():
    global _yolo
    if _yolo is None:
        from ultralytics import YOLO
        w = ROOT / "experiments" / "results" / "best_surface_cls.pt"
        if not w.exists():
            w = ROOT / "runs" / "yolo" / "surface_classify" / "weights" / "best.pt"
        _yolo = YOLO(str(w))
    return _yolo

def _load_observations():
    records = []
    if PIPELINE_DIR.exists():
        for p in PIPELINE_DIR.glob("*.json"):
            try:
                records.append(json.loads(p.read_text()))
            except Exception:
                pass
    return records

@app.get("/queue")
def queue():
    records = _load_observations()
    records.sort(key=lambda x: x.get("risk", {}).get("risk", 0), reverse=True)
    for i, r in enumerate(records):
        r["priority"] = i + 1
    return records

@app.get("/stats")
def stats():
    records = _load_observations()
    def cnt(pred): return sum(1 for r in records if pred(r))
    return {
        "inspected": len(records),
        "normal": cnt(lambda r: r.get("status") == "NORMAL"),
        "suspicious": cnt(lambda r: r.get("status") == "UNKNOWN_ABNORMALITY"),
        "known_defects": cnt(lambda r: r.get("status") == "KNOWN_DEFECT"),
        "high_risk": cnt(lambda r: r.get("risk", {}).get("level") == "HIGH"),
        "critical": cnt(lambda r: r.get("risk", {}).get("level") == "CRITICAL"),
    }

@app.post("/inspections")
async def create_inspection(
    file: UploadFile = File(...),
    chainage: float = Form(124320.0),
    track: str = Form("UP"),
    line: str = Form("LINE-01"),
):
    from ml.severity.severity_engine import compute_severity
    from ml.risk.risk_engine import compute_risk_v1
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    dest = UPLOAD_DIR / f"{uuid.uuid4().hex}_{Path(file.filename).name}"
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    yolo = get_yolo()
    res = yolo.predict(str(dest), verbose=False)[0]
    defect_type = yolo.names[res.probs.top1]
    defect_conf = float(res.probs.top1conf)
    # heuristic anomaly stand-in until RailSense inference is wired (docs/architecture/anomaly.md:64)
    anomaly = 0.85 if defect_type in ["Cracks", "Squats", "Broken"] else 0.45 if defect_type in ["Flakings", "Shellings"] else 0.25
    affected_area = {"Cracks": 0.27, "Squats": 0.31, "Flakings": 0.18, "Shellings": 0.22, "Spallings": 0.15}.get(defect_type, 0.1)
    status = "KNOWN_DEFECT" if defect_conf >= 0.5 else ("UNKNOWN_ABNORMALITY" if anomaly >= 0.5 else "NORMAL")
    sev = compute_severity(anomaly, defect_type, affected_area, "rail")
    risk = compute_risk_v1(sev["severity"], 0.95, affected_area, location_factor=0.6)
    out = {
        "image": str(dest.relative_to(ROOT)),
        "component_type": "rail",
        "known_defect": {"type": defect_type, "confidence": round(defect_conf, 3)},
        "anomaly": round(anomaly, 3),
        "status": status,
        "bbox": [0, 0, 224, 224],
        "heatmap_path": None,
        "condition": {"A": anomaly, "D": defect_type, "S": sev["severity"], "L": chainage, "Q": sev["level"]},
        "severity": sev,
        "risk": risk,
        "asset_id": f"RAIL-{chainage:g}-{track}",
        "chainage_m": chainage,
        "track_id": track,
        "line_id": line,
    }
    PIPELINE_DIR.mkdir(parents=True, exist_ok=True)
    (PIPELINE_DIR / f"{dest.stem}.json").write_text(json.dumps(out, indent=2))
    return out
