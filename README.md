# Project Chimera
Versión MVP lista para pruebas: backend (FastAPI) + Neo4j + frontend (React + Cytoscape).


## Requisitos
- Docker & Docker Compose
- (Opcional) Python 3.11 local si quieres ejecutar scripts fuera de Docker


## Levantar todo
```bash
git clone <repo>
cd project-chimera
docker-compose up --build

Neo4j: http://localhost:7474 (user: neo4j, pass: Santiago81)

API: http://localhost:8000/docs

Frontend: http://localhost:3000

Endpoints importantes

POST /ingest/evidence — Ingesta mínima de evidencia (commit, jira)

POST /team/propose — Ejecuta Algoritmo Guardián y devuelve dossiers

Pruebas sintéticas

Dentro de backend/app/scripts/generate_data.py hay un script que genera 500 empleados y carga evidencias. Ejecutar dentro del contenedor backend o localmente con conexión a Neo4j.