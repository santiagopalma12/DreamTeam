import math
from datetime import date




def recency_score_iso(iso_date_str: str) -> float:
    try:
        d = date.fromisoformat(iso_date_str)
        days = (date.today() - d).days
        return math.exp(-days / 180.0)
    except Exception:
        return 0.0




def freq_score(count: int) -> float:
    return math.log(1 + count)




def normalize(val, minv=0.0, maxv=1.0):
# keep between 0..1
    return max(0.0, min(1.0, val))




def compute_level(recency_count: int, freq_count: int, impacto: float, alpha=0.5, beta=0.3, gamma=0.2):
# recency_count expected as days_since transformed or 0..1 score
    r = recency_count
    f = freq_score(freq_count)
    i = impacto
    raw = alpha * r + beta * (math.log(1+f)) + gamma * i
    return normalize(raw)