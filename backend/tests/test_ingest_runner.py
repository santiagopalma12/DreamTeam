from app.ingestors import run


def test_run_sources_github_and_jira(monkeypatch):
    monkeypatch.setenv('GITHUB_REPOS', 'org/repo')
    monkeypatch.delenv('GITHUB_LOOKBACK_HOURS', raising=False)
    monkeypatch.setenv('JIRA_BASE', 'https://jira.example')

    class FakeResponse:
        def __init__(self, payload):
            self._payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    commits_payload = [{'sha': 'abc123', 'author': {'login': 'alice'}}]

    def fake_get(url, headers=None, params=None, timeout=30):  # noqa: D401
        return FakeResponse(commits_payload)

    captured = []

    def fake_ingest_commit(repo, sha, author):
        captured.append((repo, sha, author))

    monkeypatch.setattr(run.requests, 'get', fake_get)
    monkeypatch.setattr(run.github_ingestor, 'ingest_commit', fake_ingest_commit)
    monkeypatch.setattr(run.jira_ingestor, 'ingest_closed_issues', lambda jql: 2)

    summary = run.run_sources(['github', 'jira'], max_commits=5)

    assert summary['github']['processed_commits'] == 1
    assert summary['github']['repos'] == 1
    assert captured == [('org/repo', 'abc123', 'alice')]
    assert summary['jira']['processed_issues'] == 2


def test_run_sources_skips_when_no_config(monkeypatch):
    monkeypatch.delenv('GITHUB_REPOS', raising=False)
    monkeypatch.delenv('JIRA_BASE', raising=False)

    summary = run.run_sources(['github', 'jira'])
    assert summary['github']['processed_commits'] == 0
    assert summary['jira']['processed_issues'] == 0