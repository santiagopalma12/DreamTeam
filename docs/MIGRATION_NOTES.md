# Migration notes — Evidence nodes

This document describes the migration approach from the legacy relationship property `r.evidencias` (array of strings / JSON strings) to explicit `:Evidence` nodes.

Summary:
- `neo4j/schema.cypher` versiona constraints e índices base (Empleado, Skill, Evidence).
- `scripts/normalize_evidence_uids.py` rellena `ev.uid` con el hash determinístico (`evidence-{sha1(url|date|actor)}`) y registra colisiones.
- `neo4j/data_migrations/` almacena scripts numerados para aplicar cambios posteriores; `001_backfill_evidence_uids.cypher` documenta la verificación tras el backfill.

Post-migration plan (follow-up PR):
1. Limpiar `r.evidencias` una vez validados los `Evidence` nodes (mantener backup previo).
2. Agregar `validatedBy` y metadata adicional cuando el flujo humano esté definido (nueva migración numerada).
3. Añadir audit log o snapshot antes de la limpieza final para contar con rollback.

Testing guidance:
- Ejecutar `pytest tests/test_normalize_uids.py` para asegurar la determinación de UID e idempotencia básica.
- Realizar la normalización en staging (dry-run + apply) y luego correr el flujo ingest → recompute → propose.
