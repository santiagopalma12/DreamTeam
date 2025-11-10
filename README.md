# Project Chimera

MVP que combina backend FastAPI, Neo4j como grafo de talento y frontend React (Cytoscape) para visualizar y armar equipos. Incluye un runner de ingesta para GitHub y Jira que mantiene los niveles de habilidad actualizados.

## Requisitos
- Docker & Docker Compose
- (Opcional) Python 3.11 si quieres ejecutar scripts fuera de Docker

## Puesta en marcha
```bash
git clone <repo>
cd project-chimera
docker compose up --build
```

Servicios expuestos por defecto:
- Neo4j → http://localhost:7474 (user: `neo4j`, pass: `Santiago81`)
- API → http://localhost:8000/docs
- Frontend → http://localhost:5173/

## Endpoints clave
- `POST /ingest/evidence` – Ingesta mínima de evidencia (commit, Jira)
- `POST /team/propose` – Ejecuta Guardian y genera dossiers explicables

## Datos sintéticos
`backend/app/scripts/generate_data.py` genera ~500 empleados con evidencia. Ejecuta el script dentro del contenedor `backend` o localmente si tienes acceso a Neo4j.

## Runner de ingesta (GitHub / Jira)
Automatiza la recolección de commits e issues y re-computa habilidades. Consulta [docs/INGEST_RUNNER.md](docs/INGEST_RUNNER.md) para variables de entorno y ejemplos. Ejecución manual:

```bash
docker compose run --rm ingest-runner --sources github,jira --max-commits 10
```

El comando imprime un resumen JSON con el número de commits/issues procesados. Puedes agendarlo (cron, pipelines) según la cadencia deseada.