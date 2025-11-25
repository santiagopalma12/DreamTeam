from datetime import date

from app.guardian_dossier import build_dossier


class DummySession:
    def __init__(self, records):
        self._records = records

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def run(self, query, team):
        self.last_query = query
        self.last_team = team
        return self._records


class DummyDriver:
    def __init__(self, records):
        self._records = records

    def session(self):
        return DummySession(self._records)


def test_build_dossier_aggregates_sources_and_members():
    today = date.today().isoformat()
    records = [
        {
            "employee_id": "emp-1",
            "employee_name": "Ana",
            "employee_role": "backend",
            "skill": "Python",
            "nivel": 3.1,
            "ultima": today,
            "validado_por": "lead-1",
            "evidence_nodes": [
                {"uid": "ev-1", "date": today, "source": "github"},
                {"uid": "ev-2", "date": today, "source": "jira"},
            ],
        },
        {
            "employee_id": "emp-2",
            "employee_name": "Luis",
            "employee_role": "frontend",
            "skill": "React",
            "nivel": 2.4,
            "ultima": today,
            "validado_por": None,
            "evidence_nodes": [
                {"uid": "ev-3", "date": today, "source": "github"},
            ],
        },
    ]

    driver = DummyDriver(records)
    dossier = build_dossier(["emp-1", "emp-2"], mission_profile="investigacion", driver_instance=driver)

    assert dossier["mission_profile"] == "investigacion"
    assert dossier["summary"]["team_size"] == 2
    assert dossier["summary"]["total_evidences"] == 3

    python_skill = next(s for s in dossier["skills"] if s["skill"] == "Python")
    assert python_skill["contributors"][0]["frequency"] == 2
    assert python_skill["sources"] == {"github": 1, "jira": 1}

    react_skill = next(s for s in dossier["skills"] if s["skill"] == "React")
    assert react_skill["contributors"][0]["validated_by"] is None
    assert react_skill["contributors"][0]["recency_days"] == 0
