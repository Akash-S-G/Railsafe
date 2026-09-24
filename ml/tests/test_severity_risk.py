"""ML tests — verifies claimed severity/risk formulas per severity.md + risk.md"""
from ml.severity.severity_engine import compute_severity
from ml.risk.risk_engine import compute_risk_v1
import json
from pathlib import Path

def test_severity_formula():
    # Loose rail crack: D 0.85, A 0.81, G 0.27, C 0.95 -> S HIGH
    r = compute_severity(0.81, "Cracks", 0.27, "rail")
    assert r["level"] in ["HIGH","CRITICAL"]
    assert "contributors" in r
    assert abs(r["contributors"]["A"] - 0.35*0.81) < 0.01
    # S = w1*D + w2*A + w3*G + w4*C
    assert 0 <= r["severity"] <= 1

def test_severity_low():
    r = compute_severity(0.1, "Normal", 0.05, "sleeper")
    assert r["level"] == "LOW"
    assert r["severity"] < 0.25

def test_risk_v1_range():
    r = compute_risk_v1(0.554, 0.95, 0.18)
    assert 0 <= r["risk"] <= 100
    assert r["level"] in ["LOW","MEDIUM","HIGH","CRITICAL"]
    assert "contributors" in r
    assert "recommendation" in r

def test_risk_critical():
    r = compute_risk_v1(0.9, 0.95, 0.5, location_factor=0.9)
    assert r["level"] == "CRITICAL"
    assert r["recommendation"] == "URGENT FIELD INSPECTION"

def test_risk_explainability():
    r = compute_risk_v1(0.68, 0.85, 0.27)
    assert abs(r["contributors"]["S"] - 0.4*0.68*100) < 0.1
