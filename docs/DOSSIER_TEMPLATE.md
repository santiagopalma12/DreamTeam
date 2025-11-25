# Dossier JSON Template

El endpoint `/team/simulate` retorna un objeto con dos claves principales: `dossier` y `evaluation`. Este documento describe la forma del bloque `dossier`, encargado de explicar la evidencia del equipo.

```json
{
  "mission_profile": "investigacion",
  "team": ["emp-1", "emp-2"],
  "members": [
    {"id": "emp-1", "name": "Ana", "role": "backend"},
    {"id": "emp-2", "name": "Luis", "role": "frontend"}
  ],
  "skills": [
    {
      "skill": "Python",
      "sources": {"github": 3, "jira": 1},
      "contributors": [
        {
          "employee_id": "emp-1",
          "employee_name": "Ana",
          "employee_role": "backend",
          "nivel": 3.1,
          "ultima_demostracion": "2025-10-14",
          "recency_days": 12,
          "frequency": 4,
          "validated_by": "lead-1",
          "sources": {"github": 3, "jira": 1},
          "evidences": [
            {"uid": "evt-1", "url": "https://...", "date": "2025-10-14", "source": "github"}
          ]
        }
      ]
    }
  ],
  "summary": {
    "team_size": 2,
    "skill_count": 1,
    "total_evidences": 4,
    "average_frequency": 2.0,
    "min_frequency": 1,
    "source_breakdown": {"github": 3, "jira": 1},
    "generated_at": "2025-11-10T10:00:00Z",
    "latest_evidence": "2025-10-14"
  }
}
```

## Notas clave
- `recency_days` es el número de días desde la evidencia más reciente asociada al colaborador y la habilidad.
- `frequency` corresponde al conteo de evidencias consideradas (limitado por `evidence_limit`).
- `source_breakdown` agrega todas las fuentes a nivel de equipo para detectar dependencia en un repositorio específico.
- Si `evidence_limit` es `0`, el servidor devuelve todas las evidencias disponibles en lugar de truncarlas.
