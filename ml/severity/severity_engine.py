"""
Severity: S = w1*D + w2*A + w3*G + w4*C  (prototype, not safety thresholds)
D=defect type score, A=anomaly, G=area, C=criticality
"""
DEFECT_SCORES = {
    "Normal": 0.0, "Missing": 0.95, "Reversed": 0.6, "Displaced": 0.7,
    "Deformed": 0.8, "Broken": 0.95,  # RFDD 6
    "Grooves": 0.5, "Joints": 0.3, "Cracks": 0.85, "Flakings": 0.6,
    "Shellings": 0.65, "Spallings": 0.75, "Squats": 0.8,  # Surface 7
}
CRITICALITY = {"rail": 0.95, "fastener": 0.85, "sleeper": 0.80, "fishplate": 0.85}

def compute_severity(anomaly: float, defect_type: str | None, affected_area: float,
                     component_type: str, weights=(0.3, 0.35, 0.15, 0.20)):
    w1,w2,w3,w4 = weights
    D = DEFECT_SCORES.get(defect_type or "", 0.0)
    C = CRITICALITY.get(component_type, 0.8)
    S = w1*D + w2*anomaly + w3*affected_area + w4*C
    level = "LOW" if S<0.25 else "MEDIUM" if S<0.5 else "HIGH" if S<0.75 else "CRITICAL"
    return {"severity": round(S,3), "level": level,
            "contributors": {"D": round(w1*D,3), "A": round(w2*anomaly,3),
                             "G": round(w3*affected_area,3), "C": round(w4*C,3)}}
