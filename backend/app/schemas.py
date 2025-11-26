from pydantic import BaseModel
from typing import List, Optional, Dict


class IngestEvidence(BaseModel):
    empleado_id: str
    skill: str
    evidence_url: str
    evidence_type: Optional[str] = None
    date: Optional[str] = None


class TeamRequest(BaseModel):
    requisitos_hard: Dict
    perfil_mision: str
    k: int
    preferences: Optional[Dict] = {}