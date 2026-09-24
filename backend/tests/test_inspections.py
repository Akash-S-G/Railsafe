"""Backend tests — batch upload, past predictions, image serving per docs/architecture/dashboard.md"""
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from api.main import app, PIPELINE_DIR, UPLOAD_DIR

client = TestClient(app)

ROOT = Path(__file__).resolve().parents[2]
IMG1 = ROOT / "datasets" / "yolo_surface" / "test" / "Squats" / "7.MOV_20201228114152_5894.JPEG"
IMG2 = ROOT / "datasets" / "yolo_surface" / "test" / "Flakings" / "7.MOV_20201228114152_5081.JPEG"

@pytest.fixture()
def clean_store():
    before_pipe = set(p.name for p in PIPELINE_DIR.glob("*.json"))
    before_up = set(p.name for p in UPLOAD_DIR.glob("*"))
    yield
    for p in PIPELINE_DIR.glob("*.json"):
        if p.name not in before_pipe:
            p.unlink()
    for p in UPLOAD_DIR.glob("*"):
        if p.name not in before_up:
            p.unlink()

def test_batch_upload_roundtrip(clean_store):
    """Claim: POST /inspections accepts multiple files -> list of results"""
    assert IMG1.exists() and IMG2.exists()
    with open(IMG1, "rb") as f1, open(IMG2, "rb") as f2:
        r = client.post("/inspections",
                        files=[("files", ("a.JPEG", f1, "image/jpeg")), ("files", ("b.JPEG", f2, "image/jpeg"))],
                        data={"chainage": "999001", "track": "UP", "line": "LINE-01"})
    assert r.status_code == 200
    results = r.json()
    assert isinstance(results, list) and len(results) == 2
    assert results[0]["known_defect"]["type"] == "Squats"
    assert results[1]["known_defect"]["type"] == "Flakings"
    assert all("contributors" in x["severity"] for x in results)
    assert all("created_at" in x for x in results)

def test_past_predictions_listed(clean_store):
    with open(IMG1, "rb") as f:
        client.post("/inspections", files=[("files", ("a.JPEG", f, "image/jpeg"))], data={"chainage": "999002"})
    r = client.get("/inspections")
    assert r.status_code == 200
    past = r.json()
    assert isinstance(past, list) and len(past) >= 1
    newest = past[0]
    assert newest["known_defect"]["type"] == "Squats"
    assert newest["image"].startswith("experiments/results/uploads/")

def test_image_serving(clean_store):
    with open(IMG1, "rb") as f:
        out = client.post("/inspections", files=[("files", ("a.JPEG", f, "image/jpeg"))], data={"chainage": "999003"}).json()
    img_path = out[0]["image"]
    r = client.get(f"/image/{img_path}")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/")

def test_image_path_traversal_blocked():
    r = client.get("/image/../../etc/passwd")
    assert r.status_code in [403, 404]

def test_single_file_compat(clean_store):
    """Single 'file' field still works (backward compat)"""
    with open(IMG1, "rb") as f:
        r = client.post("/inspections", files={"file": ("a.JPEG", f, "image/jpeg")}, data={"chainage": "999004"})
    assert r.status_code == 200
    assert isinstance(r.json(), list) and len(r.json()) == 1
