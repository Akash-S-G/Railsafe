"""Backend tests — upload/queue/stats flow per docs/architecture/dashboard.md"""
import io
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from api.main import app, PIPELINE_DIR

client = TestClient(app)

IMG = Path(__file__).resolve().parents[2] / "datasets" / "yolo_surface" / "test" / "Squats" / "7.MOV_20201228114152_5894.JPEG"

@pytest.fixture()
def clean_store():
    before = set(p.name for p in PIPELINE_DIR.glob("*.json"))
    yield
    for p in PIPELINE_DIR.glob("*.json"):
        if p.name not in before:
            p.unlink()

def test_upload_inspection_roundtrip(clean_store):
    """Claim: POST /inspections runs YOLO -> severity -> risk and stores observation"""
    assert IMG.exists()
    with open(IMG, "rb") as f:
        r = client.post("/inspections", files={"file": ("test_squat.JPEG", f, "image/jpeg")},
                        data={"chainage": "999001", "track": "UP", "line": "LINE-01"})
    assert r.status_code == 200
    j = r.json()
    assert j["known_defect"]["type"] == "Squats"
    assert j["status"] == "KNOWN_DEFECT"
    assert "contributors" in j["severity"] and "contributors" in j["risk"]
    assert j["asset_id"] == "RAIL-999001-UP"

def test_queue_sorted_after_upload(clean_store):
    with open(IMG, "rb") as f:
        client.post("/inspections", files={"file": ("t.JPEG", f, "image/jpeg")}, data={"chainage": "999002"})
    r = client.get("/queue")
    assert r.status_code == 200
    q = r.json()
    risks = [x["risk"]["risk"] for x in q]
    assert risks == sorted(risks, reverse=True)

def test_stats_counts(clean_store):
    s0 = client.get("/stats").json()
    with open(IMG, "rb") as f:
        client.post("/inspections", files={"file": ("t.JPEG", f, "image/jpeg")}, data={"chainage": "999003"})
    s1 = client.get("/stats").json()
    assert s1["inspected"] == s0["inspected"] + 1
    assert s1["known_defects"] >= 1
    assert {"inspected", "normal", "suspicious", "high_risk", "critical"} <= set(s1)
