from fastapi.testclient import TestClient

from app.main import app
from app.api.routes import simulate


def test_team_simulate_endpoint(monkeypatch):
    dummy_dossier = {"mission_profile": "investigacion", "skills": []}

    def fake_build(team_ids, mission_profile=None, evidence_limit=5, driver_instance=None):
        assert team_ids == ["emp-1"]
        assert mission_profile == "investigacion"
        assert evidence_limit == 5
        return dummy_dossier

    class DummyEngine:
        def evaluate(self, dossier, overrides=None):
            return {
                "mission_profile": dossier.get("mission_profile"),
                "overall_score": 0.0,
                "weights": {},
                "thresholds": {},
                "skills": [],
                "warnings": [],
                "overrides": overrides,
            }

    monkeypatch.setattr(simulate, "build_dossier", fake_build)
    monkeypatch.setattr(simulate, "_engine", DummyEngine())

    client = TestClient(app)
    response = client.post(
        "/team/simulate",
        json={"team_ids": ["emp-1"], "mission_profile": "investigacion"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["dossier"] == dummy_dossier
    assert payload["evaluation"]["mission_profile"] == "investigacion"


def test_team_simulate_requires_team_ids(monkeypatch):
    monkeypatch.setattr(simulate, "build_dossier", lambda *args, **kwargs: {})

    client = TestClient(app)
    response = client.post("/team/simulate", json={"team_ids": []})

    assert response.status_code == 400
    assert response.json()["detail"] == "team_ids cannot be empty"
