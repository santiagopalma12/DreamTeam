from pathlib import Path

from app.policy_engine.engine import PolicyEngine


def _rules_path() -> Path:
    return Path(__file__).resolve().parent.parent / "app" / "policy_engine" / "rules.yaml"


def test_policy_engine_scores_and_warnings():
    engine = PolicyEngine(rules_path=str(_rules_path()))
    dossier = {
        "mission_profile": "investigacion",
        "skills": [
            {
                "skill": "Python",
                "contributors": [
                    {"nivel": 3.0, "frequency": 2, "recency_days": 10, "validated_by": "lead"},
                    {"nivel": 2.5, "frequency": 1, "recency_days": 15, "validated_by": None},
                ],
            }
        ],
    }

    evaluation = engine.evaluate(dossier)

    assert evaluation["mission_profile"] == "investigacion"
    assert evaluation["overall_score"] == 2.725

    skill_result = evaluation["skills"][0]
    assert skill_result["skill"] == "Python"
    assert "low_frequency" in skill_result["warnings"]
    assert skill_result["metrics"]["avg_nivel"] == 2.75


def test_policy_engine_allows_runtime_overrides():
    engine = PolicyEngine(rules_path=str(_rules_path()))
    dossier = {
        "mission_profile": "investigacion",
        "skills": [
            {
                "skill": "Python",
                "contributors": [
                    {"nivel": 3.0, "frequency": 2, "recency_days": 10, "validated_by": "lead"},
                ],
            }
        ],
    }

    overrides = {
        "weights": {
            "base_skill": 0.0,
            "nivel": 0.0,
            "frequency": 0.0,
            "validation": 0.0,
            "recency": 0.0,
        }
    }
    evaluation = engine.evaluate(dossier, overrides=overrides)

    assert evaluation["overall_score"] == 0.0
    assert evaluation["weights"]["base_skill"] == 0.0