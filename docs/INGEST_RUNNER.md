# Ingest Runner

The ingest runner executes the available evidence collectors (GitHub, Jira) on demand or on a schedule.

## Environment variables

| Variable | Description |
| --- | --- |
| `GITHUB_REPOS` | Comma separated list of repositories in the form `owner/repo`. |
| `GITHUB_TOKEN` | Personal access token with read access to the configured repositories. Optional but recommended to avoid rate limits. |
| `GITHUB_LOOKBACK_HOURS` | Optional integer lookback window. When set, commits updated within the last _n_ hours are requested. |
| `GITHUB_MAX_COMMITS` | Optional per-repository cap (default 20). |
| `JIRA_BASE` | Base URL of the Jira instance, e.g. `https://company.atlassian.net`. |
| `JIRA_USER`, `JIRA_TOKEN` | Credentials for basic auth when using Jira Cloud (API token). |
| `JIRA_JQL` | Optional JQL override. Defaults to `project = PROJ AND status = Done ORDER BY updated DESC`. |

Neo4j connection variables (`NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASS`) must also be set so the ingestors can write to the graph.

## Running locally

```bash
docker compose run --rm ingest-runner --sources github,jira --max-commits 10
```

The command prints a JSON summary with the number of commits and issues processed. Rerunning the ingestor is safe because evidence nodes are merged by deterministic `uid`.

To run directly without Docker:

```bash
python -m app.ingestors.run --sources github
```

## Scheduling

The docker-compose service is defined with the `ingest` profile so it does not start with the default stack. Attach it to a scheduler (cron, GitHub Actions, etc.) that executes the command at the desired cadence.