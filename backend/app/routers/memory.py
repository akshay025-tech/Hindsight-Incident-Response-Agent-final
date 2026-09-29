"""Memory Router: Endpoints for interacting with Hindsight operational memory."""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db, PostmortemDB
from app.services.hindsight_service import get_hindsight_service
from app.config import get_settings

router = APIRouter(prefix="/api/memory", tags=["memory"])
settings = get_settings()


class ReflectRequest(BaseModel):
    query: str
    context: Optional[str] = None


@router.get("/status")
async def memory_status():
    """Hindsight connection health and bank metadata."""
    hs = get_hindsight_service()
    health = await hs.health_check()
    return health


@router.get("/recall")
async def recall_memories(query: str = Query(..., description="Search query for incident memories")):
    """Direct query against Hindsight recall."""
    hs = get_hindsight_service()
    result = await hs.recall_similar_incidents(query)
    return result


@router.post("/reflect")
async def reflect_memory(req: ReflectRequest):
    """Reflect on historical patterns via Hindsight."""
    hs = get_hindsight_service()
    result = await hs.reflect_on_incidents(req.query, req.context)
    return result


@router.get("/library")
def get_memory_library(db: Session = Depends(get_db)):
    """
    Retrieve operational knowledge library for UI display.
    Includes retained postmortems, root causes, resolutions, and runbooks.
    """
    postmortems = db.query(PostmortemDB).order_by(PostmortemDB.created_at.desc()).all()
    memories = []

    for i, pm in enumerate(postmortems, 1):
        memories.append({
            "id": f"mem-{pm.incident_id.lower()}",
            "title": f"Incident {pm.incident_id} Resolution",
            "incident_id": pm.incident_id,
            "root_cause": pm.root_cause,
            "resolution": pm.resolution,
            "runbook": pm.runbook_used or "Standard Recovery Runbook",
            "outcome": "Successful",
            "retained_in_hindsight": pm.retained_in_hindsight,
            "retention_id": pm.hindsight_retention_id,
            "impact": pm.impact,
            "lessons_learned": pm.lessons_learned or [],
            "timestamp": pm.created_at.isoformat() if pm.created_at else None,
        })

    return {
        "bank_id": settings.hindsight_bank_id,
        "count": len(memories),
        "memories": memories,
    }
