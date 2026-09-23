"""Stub — Phase 8/9 will flesh out PostGIS queries."""
from fastapi import APIRouter
router = APIRouter()

@router.get("/")
def list_assets(line: str | None = None, chainage_from: float | None = None, chainage_to: float | None = None):
    return {"assets": [], "note": "Phase 8: query PostGIS by line + chainage range, return risk-colored pins"}

@router.get("/{component_id}")
def get_asset(component_id: str):
    return {"component_id": component_id, "history": [], "note": "Phase 9: return current observation + severity + risk contributors"}

@router.get("/{component_id}/history")
def get_history(component_id: str):
    return {"component_id": component_id, "observations": [], "temporal": "gated — requires Dataset G"}
