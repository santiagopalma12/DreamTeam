from app.uid_normalizer import EvidenceRow, apply_updates, propose_uid_updates


def test_propose_uid_updates_detects_missing_and_mismatched():
    rows = [
        EvidenceRow(node_id=1, uid=None, url="http://a", date="2025-01-01", actor="alice", source="github"),
        EvidenceRow(node_id=2, uid="evidence-bad", url="http://b", date="2025-01-01", actor="bob", source="jira"),
        EvidenceRow(node_id=3, uid="", url="http://a", date="2025-01-01", actor="alice", source="github"),
    ]

    updates, duplicates = propose_uid_updates(rows)

    assert len(updates) == 3
    # the first and third rows share the same deterministic uid -> duplicates
    shared_uid = {u["proposed_uid"] for u in updates if u["node_id"] in {1, 3}}
    assert len(shared_uid) == 1
    computed_uid = shared_uid.pop()
    assert duplicates[computed_uid] == [1, 3]


def test_apply_updates_skips_duplicates(monkeypatch):
    rows = [
        {"node_id": 1, "proposed_uid": "uid-1"},
        {"node_id": 2, "proposed_uid": "uid-duplicate"},
    ]
    duplicates = {"uid-duplicate": [2, 4]}

    calls = []

    class FakeSession:
        def run(self, query, **params):
            calls.append((query, params))

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

    class FakeDriver:
        def session(self):
            return FakeSession()

    driver = FakeDriver()

    applied = apply_updates(driver, rows, duplicates)

    assert applied == 1
    assert len(calls) == 1
    _, params = calls[0]
    assert params["node_id"] == 1
    assert params["uid"] == "uid-1"
