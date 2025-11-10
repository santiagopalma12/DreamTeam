import json
from app.scoring import compute_skill_level_from_relation


def test_compute_skill_level_monotonic():
    # empty evidences
    l0 = compute_skill_level_from_relation([], None)
    # one evidence
    l1 = compute_skill_level_from_relation(["a"], None)
    # multiple evidences
    l3 = compute_skill_level_from_relation(["a", "b", "c"], None)

    assert isinstance(l0, float) and 1.0 <= l0 <= 5.0
    assert isinstance(l1, float) and 1.0 <= l1 <= 5.0
    assert isinstance(l3, float) and 1.0 <= l3 <= 5.0
    assert l0 <= l1 <= l3


def test_compute_with_json_string_evidence_recent():
    # evidence as JSON string with a recent date should increase recency component
    recent = json.dumps({"url": "http://x", "date": "2025-11-01"})
    l_recent = compute_skill_level_from_relation([recent], None)
    l_none = compute_skill_level_from_relation(["http://x"], None)
    assert l_recent >= l_none
