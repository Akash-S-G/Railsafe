"""Backend tests — verifies claimed FastAPI endpoints per docs/architecture."""
import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_health_claim():
    """README + REQUIREMENTS_LOCK: /health returns v1 gated, no temporal until Dataset G"""
    r = client.get("/health")
    assert r.status_code == 200
    j = r.json()
    assert j["status"] == "ok"
    assert j["version"] == "v1"
    assert j["temporal"] == "gated"

def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["name"] == "RailSafe"
    assert "/health" in r.json()["health"]

def test_cors_headers():
    r = client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert r.status_code == 200
    # CORSMiddleware should allow 5173
    assert "access-control-allow-origin" in {k.lower() for k in r.headers}

def test_openapi_docs():
    r = client.get("/openapi.json")
    assert r.status_code == 200
    assert r.json()["info"]["title"] == "RailSafe API"
