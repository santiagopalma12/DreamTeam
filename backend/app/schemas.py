"""
Pydantic schemas for API requests and responses.
Phase 1: Basic schemas for employees and skills.
"""
from pydantic import BaseModel
from typing import List, Optional


class EmployeeResponse(BaseModel):
    """Employee information response."""
    id: str
    nombre: Optional[str] = None
    rol: Optional[str] = None


class EmployeeListResponse(BaseModel):
    """List of employees response."""
    employees: List[EmployeeResponse]
