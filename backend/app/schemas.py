"""
Pydantic schemas for API requests and responses.
Complete schemas for Phases 0-6.
"""
from pydantic import BaseModel
from typing import List, Optional, Dict


# Phase 1: Basic Employee Schemas
class EmployeeResponse(BaseModel):
    """Employee information response."""
    id: str
    nombre: Optional[str] = None
    rol: Optional[str] = None


class EmployeeListResponse(BaseModel):
    """List of employees response."""
    employees: List[EmployeeResponse]


# Phase 5: Executive Summary
class ExecutiveSummary(BaseModel):
    """Executive summary with top 3 pros/cons and recommendation."""
    pros: List[str]
    cons: List[str]
    recommendation: str  # APPROVE, REVIEW, or REJECT


# Phase 5: Candidate Model
class Candidate(BaseModel):
    """Team member candidate with skills and metrics."""
    id: str
    skills_matched: List[str]
    score: float
    availability_hours: Optional[int] = None
    conflict_risk: bool = False
    linchpin_risk: Optional[str] = None  # CRITICAL, HIGH, MEDIUM, LOW


# Phase 5: Dossier Model
class Dossier(BaseModel):
    """Team recommendation dossier."""
    title: str
    description: str
    executive_summary: ExecutiveSummary
    team: List[Candidate]
    total_score: float
    risk_analysis: List[str]
    rationale: str


# Phase 6: Team Request with Mission Profiles and Overrides
class TeamRequest(BaseModel):
    """Request for team recommendations."""
    requisitos_hard: Dict  # {'skills': ['Python', 'Docker']}
    k: int  # Team size
    mission_profile: Optional[str] = 'mantenimiento'  # mantenimiento, innovacion, entrega_rapida
    week: Optional[str] = None  # ISO week (e.g., '2025-W01')
    min_hours: Optional[int] = 20  # Minimum hours per week
    force_include: Optional[List[str]] = []  # Employee IDs to force-include
    force_exclude: Optional[List[str]] = []  # Employee IDs to force-exclude


# Phase 6: Mission Profile Response
class MissionProfile(BaseModel):
    """Mission profile configuration."""
    id: str
    name: str
    description: str
    strategy_preference: str
    color: str


# Phase 5: Linchpin Response
class LinchpinEmployee(BaseModel):
    """Critical employee (linchpin) with Bus Factor risk."""
    id: str
    centrality_score: float
    unique_skills: List[str]
    risk_level: str  # CRITICAL, HIGH, MEDIUM, LOW
    recommendation: str


# Legacy/Phase 2: Evidence Ingestion
class IngestEvidence(BaseModel):
    """Evidence ingestion request."""
    empleado_id: str
    skill: str
    evidence_url: str
    evidence_type: Optional[str] = None
    date: Optional[str] = None