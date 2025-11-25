# Policy Engine

El motor de políticas toma un dossier y lo pondera según reglas declarativas en `backend/app/policy_engine/rules.yaml`. El resultado se incluye en la clave `evaluation` del endpoint `/team/simulate`.

## Estructura de `rules.yaml`

```yaml
default:
  weights:
    base_skill: 1.0
    nivel: 0.4
    frequency: 0.25
    recency: -0.01
    validation: 0.5
  thresholds:
    min_frequency: 1
    max_recency_days: 120
    min_validated_ratio: 0.3
missions:
  investigacion:
    weights:
      frequency: 0.35
      recency: -0.015
    thresholds:
      min_frequency: 2
      max_recency_days: 90
```

- **weights**: ponderan factores por habilidad (`base_skill`, `nivel`, `frequency`, `recency`, `validation`).
- **thresholds**: definen mínimos/ máximos aceptables; cualquier incumplimiento genera alertas (`low_frequency`, `stale_evidence`, `low_validation`).
- **missions**: permite overrides por perfil de misión. Si no existe el perfil solicitado, el motor usa la sección `default`.

## Overrides dinámicos

El cuerpo del endpoint permite enviar overrides en caliente:

```json
{
  "team_ids": ["emp-1", "emp-2"],
  "mission_profile": "investigacion",
  "overrides": {
    "weights": {"recency": -0.02},
    "thresholds": {"max_recency_days": 60}
  }
}
```

El motor aplica los overrides después de combinar `default` y `missions`, sin mutar el archivo fuente.

## Métricas calculadas

- `avg_nivel`: promedio del nivel autocalculado por habilidad.
- `avg_frequency`: promedio de evidencias por contribuidor.
- `best_recency`: el mínimo `recency_days` encontrado para la habilidad.
- `validated_ratio`: porcentaje de contribuidores con evidencia validada.

El campo `overall_score` es la media simple de los puntajes por habilidad, redondeado a cuatro decimales.
