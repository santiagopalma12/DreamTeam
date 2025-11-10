"""CLI runner to execute data ingestors on demand or from a scheduler."""

from __future__ import annotations

import argparse
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Iterable

import requests

from . import github_ingestor, jira_ingestor

logger = logging.getLogger(__name__)


def _parse_sources(raw_sources: str | None) -> Iterable[str]:
    if not raw_sources:
        return []
    return [src.strip().lower() for src in raw_sources.split(',') if src.strip()]


def _github_headers(token: str | None) -> Dict[str, str]:
    if token:
        return {"Authorization": f"token {token}"}
    return {}


def run_github(max_commits: int | None = None) -> Dict[str, int]:
    repos = [r.strip() for r in os.getenv('GITHUB_REPOS', '').split(',') if r.strip()]
    if not repos:
        logger.info('No GITHUB_REPOS configured; skipping GitHub ingestion.')
        return {'processed_commits': 0, 'repos': 0}

    token = os.getenv('GITHUB_TOKEN')
    headers = _github_headers(token)

    lookback_env = os.getenv('GITHUB_LOOKBACK_HOURS')
    since_param = None
    if lookback_env:
        try:
            hours = int(lookback_env)
            if hours > 0:
                since_dt = datetime.utcnow() - timedelta(hours=hours)
                since_param = since_dt.isoformat() + 'Z'
        except ValueError:
            logger.warning('Invalid GITHUB_LOOKBACK_HOURS=%s (ignored)', lookback_env)

    if max_commits is None:
        try:
            max_commits = int(os.getenv('GITHUB_MAX_COMMITS', '20'))
        except ValueError:
            max_commits = 20

    processed = 0
    for repo in repos:
        params = {'per_page': max_commits}
        if since_param:
            params['since'] = since_param
        url = f'https://api.github.com/repos/{repo}/commits'
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=30)
            resp.raise_for_status()
            commits = resp.json()
        except Exception as exc:  # pragma: no cover - network errors handled gracefully
            logger.error('GitHub fetch failed for %s: %s', repo, exc)
            continue

        for commit in commits:
            sha = commit.get('sha')
            author_login = (
                commit.get('author', {}) or {}
            ).get('login') or commit.get('commit', {}).get('author', {}).get('email')
            if not sha or not author_login:
                continue
            try:
                github_ingestor.ingest_commit(repo, sha, author_login)
                processed += 1
            except Exception as exc:  # pragma: no cover - ingestion errors should not stop runner
                logger.error('GitHub ingest failed for %s@%s: %s', repo, sha, exc)

    return {'processed_commits': processed, 'repos': len(repos)}


def run_jira() -> Dict[str, int]:
    if not os.getenv('JIRA_BASE'):
        logger.info('JIRA_BASE not configured; skipping Jira ingestion.')
        return {'processed_issues': 0}

    jql = os.getenv('JIRA_JQL', 'project = PROJ AND status = Done ORDER BY updated DESC')
    try:
        processed = jira_ingestor.ingest_closed_issues(jql=jql) or 0
    except Exception as exc:  # pragma: no cover - network errors handled gracefully
        logger.error('Jira ingest failed: %s', exc)
        processed = 0
    return {'processed_issues': processed}


def run_sources(sources: Iterable[str], max_commits: int | None = None) -> Dict[str, Dict[str, int]]:
    summary: Dict[str, Dict[str, int]] = {}
    for source in sources:
        if source == 'github':
            summary['github'] = run_github(max_commits=max_commits)
        elif source == 'jira':
            summary['jira'] = run_jira()
        else:
            logger.warning('Unknown ingest source: %s', source)
    return summary


def cli(argv: list[str] | None = None) -> Dict[str, Dict[str, int]]:
    parser = argparse.ArgumentParser(description='Run Project Chimera ingestors')
    parser.add_argument('--sources', default='github,jira', help='Comma separated sources to run (github,jira)')
    parser.add_argument('--max-commits', type=int, help='Limit GitHub commits per repo (overrides env)')
    parser.add_argument('--log-level', default=os.getenv('INGEST_LOG_LEVEL', 'INFO'), help='Logging level (INFO, DEBUG, ...)')

    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, (args.log_level or 'INFO').upper(), logging.INFO),
                        format='[%(levelname)s] %(message)s')

    sources = list(_parse_sources(args.sources))
    if not sources:
        logger.warning('No sources requested. Nothing to do.')
        return {}

    summary = run_sources(sources, max_commits=args.max_commits)
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == '__main__':  # pragma: no cover
    cli()