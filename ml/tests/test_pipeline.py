"""Pipeline tests — verifies claimed end-to-end artifacts per README pipeline"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def test_yolo_model_exists():
    """Claim: YOLO11n-cls 3.1M trained, saved to experiments/results"""
    assert (ROOT / "experiments" / "results" / "best_surface_cls.pt").exists()
    assert (ROOT / "experiments" / "results" / "best_surface_cls.pt").stat().st_size > 1_000_000

def test_manifest_grouped_no_leakage():
    """Claim: leakage.md grouped by sequence_id, manifest 6011 records, no leakage"""
    manifest = ROOT / "datasets" / "manifest.jsonl"
    assert manifest.exists()
    recs = [json.loads(l) for l in manifest.read_text().splitlines() if l.strip()]
    assert len(recs) == 6011
    from collections import defaultdict
    groups = defaultdict(set)
    for r in recs:
        groups[(r["dataset_id"], r["sequence_id"])].add(r["split"])
    leaked = [k for k,v in groups.items() if len(v)>1]
    assert leaked == [], f"Leaked groups: {leaked}"

def test_yolo_surface_layout():
    """Claim: 7 classes in all splits after prepare_yolo fix"""
    for split in ["train","val","test"]:
        p = ROOT / "datasets" / "yolo_surface" / split
        assert p.exists(), f"Missing {p}"
        classes = {d.name for d in p.iterdir() if d.is_dir()}
        assert len(classes) == 7, f"{split} has {classes}, requires 7"

def test_queue_ranked():
    """Claim: asset-centric queue sorted by R descending per risk.md"""
    q = json.loads((ROOT / "experiments" / "results" / "queue.json").read_text())
    assert len(q) >= 1
    risks = [r["risk"]["risk"] for r in q]
    assert risks == sorted(risks, reverse=True), "Queue not sorted by risk"
    assert all("contributors" in r["risk"] for r in q)

def test_pipeline_output():
    """Claim: integrated pipeline produces Ct=[A,D,S,L,Q] + contributors"""
    pipeline_dir = ROOT / "experiments" / "results" / "pipeline"
    assert pipeline_dir.exists()
    sample = next(pipeline_dir.glob("*.json"), None)
    assert sample is not None
    j = json.loads(sample.read_text())
    assert "severity" in j and "risk" in j
    assert "contributors" in j["severity"]
    assert "contributors" in j["risk"]
    assert j["risk"]["level"] in ["LOW","MEDIUM","HIGH","CRITICAL"]
