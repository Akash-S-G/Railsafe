"""
Risk v1: R = w1*S + w2*C + w3*A + w4*L  (D=0 gated for v1)
Risk v2: R = w1*S + w2*D + w3*C + w4*A + w5*L  (D from temporal, gated)
R in [0,100] -> LOW 0-25 / MEDIUM 25-50 / HIGH 50-75 / CRITICAL 75-100
All thresholds are RailSafe decision-support, NOT safety limits.
"""

def compute_risk_v1(severity: float, criticality: float, affected_area: float,
                    location_factor: float = 0.5, weights=(0.4, 0.25, 0.20, 0.15)):
    w1,w2,w3,w4 = weights
    R = w1*severity + w2*criticality + w3*affected_area + w4*location_factor
    R100 = round(R*100, 1)
    level = "LOW" if R100<25 else "MEDIUM" if R100<50 else "HIGH" if R100<75 else "CRITICAL"
    rec = {"LOW":"CONTINUE ROUTINE MONITORING","MEDIUM":"SCHEDULED INSPECTION",
           "HIGH":"PRIORITY INSPECTION","CRITICAL":"URGENT FIELD INSPECTION"}[level]
    return {"risk": R100, "level": level, "recommendation": rec,
            "contributors": {"S": round(w1*severity*100,1), "C": round(w2*criticality*100,1),
                             "A": round(w3*affected_area*100,1), "L": round(w4*location_factor*100,1)}}
