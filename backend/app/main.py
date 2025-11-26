"""
Project Chimera - Smart Team Assembly Engine
Main FastAPI application with all Phase 0-6 endpoints.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .db import get_driver
from .schemas import (
    TeamRequest, Dossier, EmployeeListResponse, EmployeeResponse,
    LinchpinEmployee, MissionProfile
)
from .guardian_core import generate_dossiers
from .linchpin_detector import detect_linchpins
from .mission_profiles import MISSION_PROFILES
from .scoring import recompute_all_skill_levels
from .uid_normalizer import normalize_all_employees
import uuid

app = FastAPI(
    title="Project Chimera",
    description="Smart Team Assembly Engine - Evidence-based team recommendations",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    """Health check endpoint."""
    return {
        "message": "Project Chimera API",
        "version": "1.0.0",
        "status": "operational"
    }


# ============================================================================
# GUARDIAN ENDPOINTS (Phase 5-6)
# ============================================================================

@app.post("/api/recommend", response_model=Dict)
def recommend_teams(request: TeamRequest):
    """
    Generate team recommendations based on requirements and mission profile.
    
    Phase 5: Guardian Co-Pilot Mode
    Phase 6: Policy & Governance (mission profiles, overrides)
    """
    try:
        dossiers = generate_dossiers(request.dict())
        return {
            "request_id": str(uuid.uuid4()),
            "dossiers": [d.dict() for d in dossiers]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/linchpins")
def get_linchpins():
    """
    Get list of critical employees (linchpins) with Bus Factor risk.
    
    Phase 5: Guardian Co-Pilot Mode
    """
    try:
        linchpins = detect_linchpins()
        return {
            "linchpins": linchpins,
            "count": len(linchpins)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/mission-profiles")
def get_mission_profiles():
    """
    Get available mission profiles.
    
    Phase 6: Policy & Governance
    """
    profiles = []
    for profile_id, config in MISSION_PROFILES.items():
        profiles.append({
            "id": profile_id,
            "name": config["name"],
            "description": config["description"],
            "strategy_preference": config["strategy_preference"],
            "color": config.get("color", "#4CAF50")
        })
    return {"profiles": profiles}


# ============================================================================
# ADMIN ENDPOINTS (Phase 4)
# ============================================================================

@app.post("/admin/recompute-skills")
def recompute_skills():
    """
    Recalculate skill levels for all employees.
    
    Phase 4: Contextual Scoring Engine
    Warning: This can be slow for large datasets.
    """
    try:
        driver = get_driver()
        result = recompute_all_skill_levels(driver)
        return {
            "ok": True,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/admin/normalize")
def normalize_uids():
    """
    Re-normalize all employee UIDs in the graph.
    
    Phase 3: Privacy & Normalization
    Warning: This is a destructive operation. Backup database first.
    """
    try:
        result = normalize_all_employees()
        return {
            "ok": True,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# QUERY ENDPOINTS (Phase 1)
# ============================================================================

@app.get("/employees", response_model=EmployeeListResponse)
def list_employees():
    """
    List all employees in the system.
    
    Phase 1: Graph & Taxonomy
    """
    query = """
    MATCH (e:Empleado)
    RETURN e.id as id, e.nombre as nombre, e.rol as rol
    ORDER BY e.id
    """
    employees = []
    driver = get_driver()
    with driver.session() as session:
        result = session.run(query)
        for record in result:
            employees.append({
                'id': record['id'],
                'nombre': record.get('nombre'),
                'rol': record.get('rol')
            })
    return {"employees": employees}


# ============================================================================
# SHUTDOWN EVENT
# ============================================================================

@app.on_event("shutdown")
def shutdown_event():
    """Close database connection on shutdown."""
    from .db import close_driver
    close_driver()
