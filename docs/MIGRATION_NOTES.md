# Migration notes — Evidence nodes

This document describes the migration approach from the legacy relationship property `r.evidencias` (array of strings / JSON strings) to explicit `:Evidence` nodes.

Summary:
- A migration script `scripts/migrate_evidences_to_nodes.py` is included in the repo.
- The script creates `:Evidence` nodes with properties (uid, url, date, actor, type, source, raw) and connects them to the employee and skill with relationships.
- The script marks processed relationships (adds `r._migrated = true`) to avoid reprocessing.

Post-migration plan (follow-up PR):
1. Normalize `uid` values for legacy evidence (make them deterministic e.g. `evidence-{sha1(url+date+actor)}`) and store them on Evidence nodes.
2. Remove legacy `r.evidencias` arrays once all Evidence nodes are present and verified.
3. Add an audit log or snapshot before the cleanup for rollback.

Testing guidance:
- Run the integration tests which exercise ingest -> recompute -> propose flow.
- Perform migration in a staging DB first and run `guardian.propose_teams` to verify evidences surface in dossiers.
