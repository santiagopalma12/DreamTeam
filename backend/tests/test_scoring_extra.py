import json
from datetime import date, timedelta
from app.scoring import (
    compute_skill_level_from_relation,
    _compute_freq_score,
    _compute_recency_score,
    make_evidence_uid,
)


def test_freq_saturation():
    # frequency score should saturate as n grows
    small = _compute_freq_score(1)
    medium = _compute_freq_score(5)
    large = _compute_freq_score(50)
    assert 0.0 <= small <= 1.0
    assert small < medium
    # large should be close to 1.0 (saturated)
    assert large <= 1.0 and large >= 0.9


def test_recency_edge_cases():
    # recent (today) should be near 1.0
    assert _compute_recency_score(0) == 1.0
    # one year old should be near 0
    assert _compute_recency_score(365) == 0.0
    # unknown days returns default
    assert _compute_recency_score(None) == 0.2


def test_compute_with_ultima_override():
    # If ultima provided (recent), it should increase level versus old inferred
    old_date = (date.today() - timedelta(days=800)).isoformat()
    recent_date = date.today().isoformat()
    evs = [json.dumps({"url": "x", "date": old_date})]
    l_old = compute_skill_level_from_relation(evs, None)
    l_recent = compute_skill_level_from_relation(evs, recent_date)
    assert l_recent >= l_old


def test_make_evidence_uid_deterministic():
    a = make_evidence_uid('http://x', '2025-01-01', 'alice')
    b = make_evidence_uid('http://x', '2025-01-01', 'alice')
    c = make_evidence_uid('http://x', '2025-01-02', 'alice')
    assert a == b
    assert a != c
