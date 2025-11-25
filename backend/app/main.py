"""
Project Chimera - Smart Team Assembly Engine
Phase 0: Foundation & Schema
"""
from fastapi import FastAPI
from .db import close_driver

app = FastAPI(
    title="Project Chimera",
    description="Smart Team Assembly Engine - Evidence-based team recommendations",
    version="0.1.0"
)


@app.on_event("shutdown")
def shutdown_event():
    """Close database connection on shutdown."""
    close_driver()


@app.get("/")
def root():
    """Health check endpoint."""
    return {"message": "Project Chimera API - Phase 0: Foundation"}
