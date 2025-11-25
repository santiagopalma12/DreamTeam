# Phase 1 Backlog – Schema Foundation

> Use this checklist to create GitHub issues. Each item includes a suggested title, description outline, acceptance criteria, and labels.

## 1. Define Neo4j Schema Baseline
- **Suggested Title:** `[P1][Schema] Define GRO constraints and indexes`
- **Summary:** Draft `backend/neo4j/schema.cypher` capturing labels (`Empleado`, `Skill`, `Evidence`) and relationship constraints (`DEMUESTRA_COMPETENCIA`, `HAS_EVIDENCE`, `ABOUT`, `HA_COLABORADO_CON`). Document property requirements (uid uniqueness, required fields) and index strategy for mission profiles.
- **Acceptance Criteria:**
  - `schema.cypher` checked in with idempotent constraints and indexes.
  - README or doc section referencing how to apply schema.
  - Unit doc/test verifying expected constraints exist via Cypher query.
- **Labels:** `phase:1-schema`, `component:neo4j`, `priority:high`

## 2. Migration & Validation Script
- **Suggested Title:** `[P1][Schema] Implement schema migration runner`
- **Summary:** Build `scripts/apply_schema.py` (or similar) that executes the Cypher schema file against the running Neo4j instance with logging and dry-run mode.
- **Acceptance Criteria:**
  - Script can be run locally (`python scripts/apply_schema.py`) and logs applied/ skipped operations.
  - Handles failure gracefully and exits non-zero on error.
  - Added instructions to `docs/OPERATIONS.md` (or README) on usage.
- **Labels:** `phase:1-schema`, `component:ops`, `priority:high`

## 3. Skill Taxonomy Loader
- **Suggested Title:** `[P1][Schema] Seed canonical skill taxonomy`
- **Summary:** Introduce CSV/JSON defining skill families, aliases, and canonical names. Provide loader script that upserts `Skill` nodes with taxonomy metadata.
- **Acceptance Criteria:**
  - Taxonomy file published under `data/skills_taxonomy.csv` (or similar).
  - Loader script populates `Skill` nodes and attaches properties (`family`, `aliases`).
  - Tests/verification queries demonstrating taxonomy applied.
- **Labels:** `phase:1-schema`, `component:data`, `priority:medium`

## 4. Backfill Existing Data to Schema
- **Suggested Title:** `[P1][Schema] Backfill legacy GRO data to new schema`
- **Summary:** Write Cypher script(s) that reconcile current nodes/relationships with new constraints (e.g., ensure every Evidence has UID, attach taxonomy attributes, normalize property names).
- **Acceptance Criteria:**
  - Script(s) located in `scripts/migrations/` and idempotent.
  - Validation report confirming zero constraint violations post-run.
  - Snapshot diff (Cypher output) attached to issue comment for audit.
- **Labels:** `phase:1-schema`, `component:migrations`, `priority:high`

## 5. Automated Schema Integrity Test
- **Suggested Title:** `[P1][Schema] Add schema integrity pytest`
- **Summary:** Create test that connects to test Neo4j instance (or mocks) verifying constraints/indexes, required properties, and taxonomy markers.
- **Acceptance Criteria:**
  - New test file `backend/tests/test_schema_integrity.py` (or similar).
  - Test executed in CI (failing intentionally when schema inconsistent).
  - Document how to run test locally with ephemeral Neo4j.
- **Labels:** `phase:1-schema`, `component:testing`, `priority:medium`

## 6. Schema Documentation & Runbook
- **Suggested Title:** `[P1][Schema] Document GRO schema and operations`
- **Summary:** Produce `docs/GRO_SCHEMA.md` describing node/relationship types, property semantics, ingestion expectations, and how schema ties to mission profiles.
- **Acceptance Criteria:**
  - Doc committed under `docs/` with diagrams/tables as needed.
  - README references new doc and schema application steps.
  - Includes checklist for validating schema after migrations.
- **Labels:** `phase:1-schema`, `component:docs`, `priority:medium`

---

> After creating the GitHub issues, link them to the pinned freeze notice and assign owners/dates per steering decisions.
