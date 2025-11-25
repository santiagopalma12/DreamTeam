from __future__ import annotations

from backend.app.ingestors import pipeline


def test_normalize_evidence_uids(monkeypatch):
    fake_driver = object()
    rows = [object()]
    updates = [
        {"node_id": 1, "current_uid": "old", "proposed_uid": "new", "url": "u", "date": "d", "actor": "a", "source": "s"}
    ]
    duplicates = {"dup": [1, 1, 2]}

    monkeypatch.setattr(pipeline, "get_driver", lambda: fake_driver)
    monkeypatch.setattr(pipeline, "fetch_evidence_rows", lambda driver: rows)
    monkeypatch.setattr(pipeline, "propose_uid_updates", lambda fetched: (updates, duplicates))

    captured = {}

    def fake_apply(driver, incoming_updates, incoming_duplicates):
        captured["driver"] = driver
        captured["updates"] = list(incoming_updates)
        captured["duplicates"] = incoming_duplicates
        return 1

    monkeypatch.setattr(pipeline, "apply_updates", fake_apply)

    summary = pipeline._normalize_evidence_uids()
    assert captured["driver"] is fake_driver
    assert captured["updates"] == updates
    assert summary == {"scanned": 1, "proposed": 1, "applied": 1, "blocked": {"dup": [1, 2]}}


def test_run_pipeline_respects_skip_flags(monkeypatch):
    called = {"ingest": False, "normalize": False, "recompute": False}
    ingest_calls: list[tuple[list[str], int | None]] = []

    def fake_run_sources(sources, max_commits=None):
        called["ingest"] = True
        ingest_calls.append((list(sources), max_commits))
        return {"github": {"processed_commits": 3}}

    monkeypatch.setattr(pipeline, "run_sources", fake_run_sources)
    monkeypatch.setattr(
        pipeline,
        "_normalize_evidence_uids",
        lambda: called.__setitem__("normalize", True) or {"applied": 0},
    )
    monkeypatch.setattr(
        pipeline,
        "recompute_all_skill_levels",
        lambda driver: called.__setitem__("recompute", True) or {"updated": 0},
    )
    monkeypatch.setattr(pipeline, "get_driver", lambda: object())

    summary = pipeline.run_pipeline(["github"], max_commits=5, skip_normalization=True, skip_recompute=True)

    assert called == {"ingest": True, "normalize": False, "recompute": False}
    assert ingest_calls == [(["github"], 5)]
    assert summary == {"ingest": {"github": {"processed_commits": 3}}}

    # now run with normalization and recompute enabled
    summary = pipeline.run_pipeline(["github"], max_commits=None, skip_normalization=False, skip_recompute=False)
    assert called["normalize"] is True
    assert called["recompute"] is True
    assert ingest_calls[-1] == (["github"], None)
    assert "normalize" in summary and "recompute" in summary