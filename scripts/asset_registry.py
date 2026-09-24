#!/usr/bin/env python3
"""
Phase 8-9: Asset Registry — maps pipeline output -> PostGIS (if available) else JSON file.
Creates ranked queue sorted by risk.

Usage:
  python ml/pipeline/integrated_pipeline.py --image datasets/yolo_surface/test/Squats/*.JPEG
  python scripts/asset_registry.py --input experiments/results/pipeline/ --output experiments/results/queue.json
"""
import argparse, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "experiments" / "results" / "queue.json"
ASSETS_DB = ROOT / "experiments" / "results" / "assets.json"

def build_queue(input_dir: Path):
    records = []
    for p in Path(input_dir).glob("*.json"):
        try:
            r = json.loads(p.read_text())
            records.append(r)
        except: pass
    # if no pipeline outputs, create demo from 3 samples
    if not records:
        print(f"No pipeline outputs in {input_dir}, creating demo queue")
        # run pipeline on 3 samples
        import subprocess, sys
        samples = list((ROOT/"datasets"/"yolo_surface"/"test").rglob("*.JPEG"))[:3]
        for s in samples:
            subprocess.run([sys.executable, "ml/pipeline/integrated_pipeline.py", "--image", str(s)], cwd=ROOT)
        for p in Path(input_dir).glob("*.json"):
            records.append(json.loads(p.read_text()))
    # rank by risk descending
    records.sort(key=lambda x: x.get("risk",{}).get("risk",0), reverse=True)
    for i, r in enumerate(records):
        r["priority"] = i+1
    # save queue
    QUEUE.write_text(json.dumps(records, indent=2))
    ASSETS_DB.write_text(json.dumps({r["asset_id"]: r for r in records}, indent=2))
    print(f"Queue -> {QUEUE} ({len(records)} assets)")
    for r in records[:5]:
        print(f"  Priority {r['priority']}: {r['asset_id']} {r['risk']['risk']} {r['risk']['level']} {r['known_defect']['type']}")
    # Try PostGIS insert (optional)
    try:
        import psycopg2
        # connection from backend/.env
        env = {}
        if (ROOT/"backend"/".env").exists():
            for line in (ROOT/"backend"/".env").read_text().splitlines():
                if "=" in line and not line.startswith("#"):
                    k,v = line.strip().split("=",1)
                    env[k]=v
        url = env.get("DATABASE_URL", "postgresql://railsafe:railsafe@localhost:5432/railsafe")
        # parse
        print(f"PostGIS try: {url.split('@')[-1]}")
        conn = psycopg2.connect(url.replace("postgresql+psycopg2://","postgresql://"))
        cur = conn.cursor()
        cur.execute("SELECT 1")
        print("PostGIS reachable — would insert assets (skipped in CPU demo)")
        conn.close()
    except Exception as e:
        print(f"PostGIS not available (ok for JSON demo): {e}")
    return records

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, default=ROOT/"experiments"/"results"/"pipeline")
    ap.add_argument("--output", type=Path, default=QUEUE)
    args = ap.parse_args()
    build_queue(args.input)
