# NORMALIZE_UIDS

Descripción
-----------
Este documento acompaña el script `scripts/normalize_evidence_uids.py`. El objetivo es asignar un `uid` determinístico a nodos `:Evidence` que actualmente no tengan `uid`, usando la convención `evidence-{sha1(url|date|actor)}`.

Modo de uso
-----------
- Dry-run (por defecto): lista los nodos `Evidence` que no tienen `uid` y muestra el `uid` propuesto sin modificar la BD. Puedes exportar el listado con `--export-csv`.

  ```bash
  python scripts/normalize_evidence_uids.py --export-csv /tmp/proposed_uids.csv
  ```

- Aplicar cambios: ejecuta con `--apply` y confirma escribiendo `YES` cuando se te pida.

  ```bash
  python scripts/normalize_evidence_uids.py --apply --export-csv /tmp/proposed_uids.csv
  ```

Garantías y seguridad
---------------------
- No se eliminan ni modifican propiedades legacy (`r.evidencias`) en esta operación.
- El script sólo establece `ev.uid` en nodos que no tienen `uid` para evitar sobreescrituras.
- Recomendado ejecutar primero en staging y revisar el listado propuesto.

Recomendaciones adicionales
---------------------------
- Generar un CSV de auditoría previo al `--apply` (opcional): exporta id interno, url, date, actor y uid propuesto.
- Hacer snapshot/export de la base Neo4j antes de aplicar (dump o copia del volumen).
- Ejecutar tests de idempotencia: volver a ejecutar el script en modo `--apply` debe no proponer cambios adicionales.

Política de UID
--------------
Actualmente el uid se genera con `make_evidence_uid(url, date, actor)` y tiene formato `evidence-{sha1}`. Si quieres otra convención
(por ejemplo `ev-{shorthash}` o incluir parte legible), indícalo ahora y adapto el script.

Follow-up
---------
Una vez verificado en staging y con reviewers conformes, crearé un PR separado para ejecutar la limpieza final de `r.evidencias` y un plan de rollback.
