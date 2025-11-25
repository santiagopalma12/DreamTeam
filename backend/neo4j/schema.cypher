// --- Constraints ---

// Empleado: ID must be unique (e.g. 'juan.perez' or hash)
CREATE CONSTRAINT unique_empleado_id IF NOT EXISTS FOR (e:Empleado) REQUIRE e.id IS UNIQUE;

// Skill: Name must be unique (e.g. 'Python')
CREATE CONSTRAINT unique_skill_name IF NOT EXISTS FOR (s:Skill) REQUIRE s.name IS UNIQUE;

// Evidence: UID must be unique (deterministic hash)
CREATE CONSTRAINT unique_evidence_uid IF NOT EXISTS FOR (ev:Evidence) REQUIRE ev.uid IS UNIQUE;

// Availability: Slot ID (e.g. '2024-W42') could be unique per employee, but globally we might just index it.
// Let's constrain the Slot node itself if we share them, or just index if they are per-employee.
// For now, we assume Availability nodes are per-employee-slot, so no global uniqueness on ID unless we generate a composite ID.
CREATE INDEX index_availability_week IF NOT EXISTS FOR (a:Availability) ON (a.week);

// --- Indexes ---

// Performance indexes
CREATE INDEX index_evidence_date IF NOT EXISTS FOR (ev:Evidence) ON (ev.date);
CREATE INDEX index_evidence_source IF NOT EXISTS FOR (ev:Evidence) ON (ev.source);
CREATE INDEX index_skill_family IF NOT EXISTS FOR (s:Skill) ON (s.family);

// Validation & Impact
CREATE INDEX index_evidence_validado_por IF NOT EXISTS FOR (ev:Evidence) ON (ev.validadoPor);
CREATE INDEX index_evidence_impacto IF NOT EXISTS FOR (ev:Evidence) ON (ev.impacto);

// Phase 5: ManualConstraint support (HR overrides)
// Allows HR to veto specific pairings: (A)-[:MANUAL_CONSTRAINT {reason: "Past conflict"}]->(B)
CREATE INDEX index_manual_constraint_source IF NOT EXISTS FOR ()-[r:MANUAL_CONSTRAINT]-() ON (r.source);
