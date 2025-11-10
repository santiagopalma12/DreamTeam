# Neo4j data migrations

Place ordered Cypher scripts in this directory (e.g. `001_normalize_evidence_uids.cypher`).
Each script should be idempotent because migrations may run more than once in staging
and production environments.

Suggested workflow:

1. Run `schema.cypher` to ensure constraints and indexes exist.
2. Apply numbered migration files in lexical order.
3. Track the last applied migration in release notes or an operations log.
