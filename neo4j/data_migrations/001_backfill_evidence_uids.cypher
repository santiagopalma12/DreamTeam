// Migration 001 — record of Evidence uid backfill
//
// This migration accompanies `scripts/normalize_evidence_uids.py`. Run the Python
// helper first to compute deterministic `uid` values, then optionally execute
// follow-up Cypher to validate results.
//
// Example validation: list Evidence nodes still missing uid after running the script.
MATCH (ev:Evidence)
WHERE ev.uid IS NULL
RETURN id(ev) AS node_id, ev.url AS url
LIMIT 25;
