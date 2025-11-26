from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .db import driver
from .schemas import IngestEvidence, TeamRequest
from .ingestors.github_ingestor import ingest_commit
from .guardian import propose_teams, filter_candidates
from .scoring import recompute_all_skill_levels, recompute_skill_levels_for_employees

app = FastAPI(title="Project Chimera API")

# Allow frontend dev server to call the API (adjust origins for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/ingest/evidence")
async def ingest_evidence(e: IngestEvidence):
    # crea/actualiza nodo Skill y relación DEMUESTRA_COMPETENCIA con evidence
    with driver.session() as session:
        cypher = """
        MERGE (emp:Empleado {id:$eid})
        MERGE (sk:Skill {name:$skill})
        MERGE (emp)-[r:DEMUESTRA_COMPETENCIA]->(sk)
        ON CREATE SET r.evidencias = [], r.nivel=0.0, r.ultimaDemostracion = date($date)
        WITH r
        CALL {
          WITH r
          SET r.evidencias = coalesce(r.evidencias, []) + [$url]
          SET r.ultimaDemostracion = date($date)
          RETURN r
        }
        RETURN r
        """
        session.run(cypher, eid=e.empleado_id, skill=e.skill, url=e.evidence_url, date=e.date or "2025-01-01")
    return {"ok": True}

@app.post("/team/propose")
async def team_propose(req: TeamRequest):
    # Filtra candidatos por hard requirements
    payload = req.dict()
    hard = payload.get('requisitos_hard', {})
    try:
        candidates_raw = filter_candidates(hard)
        candidate_ids = [c['id'] for c in candidates_raw]
    except Exception:
        candidate_ids = []

    # Recompute skill levels only for the candidates involved (on-demand, efficient)
    if candidate_ids:
        try:
            recompute_skill_levels_for_employees(driver, candidate_ids)
        except Exception as e:
            # don't fail the request; log and continue
            print('warning: recompute skill levels failed', e)

    # call the guardian algorithm
    proposals = propose_teams(payload)
    return {"proposals": proposals}


@app.get("/employees")
async def list_employees():
    # devuelve lista simple de empleados para visualización en frontend
    q = """
    MATCH (e:Empleado)
    RETURN e.id as id, e.nombre as nombre, e.rol as rol
    ORDER BY e.id
    """
    out = []
    with driver.session() as s:
        res = s.run(q)
        for r in res:
            out.append({ 'id': r['id'], 'nombre': r.get('nombre'), 'rol': r.get('rol') })
    return { 'employees': out }


@app.post("/admin/recompute-skills")
async def admin_recompute_skills():
    """Recompute skill levels for all DEMUESTRA_COMPETENCIA relationships (admin endpoint)."""
    res = recompute_all_skill_levels(driver)
    return { 'ok': True, 'result': res }
