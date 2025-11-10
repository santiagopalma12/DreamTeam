// Base schema constraints and indexes for Project Chimera

// Employee
CREATE CONSTRAINT employee_id_unique IF NOT EXISTS
FOR (e:Empleado)
REQUIRE e.id IS UNIQUE;

// Skill
CREATE CONSTRAINT skill_name_unique IF NOT EXISTS
FOR (s:Skill)
REQUIRE s.name IS UNIQUE;

// Evidence nodes store normalized uid
CREATE CONSTRAINT evidence_uid_unique IF NOT EXISTS
FOR (ev:Evidence)
REQUIRE ev.uid IS UNIQUE;

// Optional lookup indexes to speed up queries
CREATE INDEX evidence_source_lookup IF NOT EXISTS
FOR (ev:Evidence)
ON (ev.source);

CREATE INDEX evidence_actor_lookup IF NOT EXISTS
FOR (ev:Evidence)
ON (ev.actor);

CREATE INDEX evidence_date_lookup IF NOT EXISTS
FOR (ev:Evidence)
ON (ev.date);
