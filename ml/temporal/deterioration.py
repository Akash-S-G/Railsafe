"""Deterioration — GATED (requires Dataset G)."""
# Baseline: C(t) = beta0 + beta1*t ; beta1>0 deteriorating
# Then EMA / Kalman; LSTM only if n sufficient — never start with LSTM
def estimate_trend(history: list[float]):
    raise NotImplementedError("GATED — requires >=4 observations per asset")
