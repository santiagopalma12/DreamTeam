<!-- Use this template to describe the purpose of the pull request and provide a quick checklist. -->

## Descripción breve

Por favor describe brevemente los cambios y la motivación.

## Cambios incluidos
- Migración parcial de evidencias a nodos `:Evidence` (script incluido)
- Ingestors actualizados para crear `Evidence` nodes
- `guardian` ahora incluye justificaciones con evidencias estructuradas
- Tests unitarios e integración añadidos

## Checklist antes de merge
- [ ] Los checks de CI (pytest) pasan
- [ ] Revisar migración: `scripts/migrate_evidences_to_nodes.py` y `docs/MIGRATION_NOTES.md`
- [ ] Confirmar que la normalización de `uid` se hará en un PR separado
- [ ] Asignar reviewers y aprobar cambios
- [ ] (Opcional) Ejecutar migración en entorno staging y verificar dossiers

## Notas de despliegue / migración
Por seguridad, la normalización de `uid` y la limpieza final de `r.evidencias` se hará en un PR aparte tras la aprobación y verificación en CI.
