"""Agents Router: Autonomous AI investigation and analysis endpoints."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db, IncidentDB, utc_now
from app.models.analysis import AnalysisResult
from app.models.incident import IncidentStatus
from app.agents.incident_agent import get_incident_agent

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.post("/analyze/{incident_id}", response_model=AnalysisResult)
async def analyze_incident_endpoint(
    incident_id: str,
    db: Session = Depends(get_db),
):
    """
    Trigger full AI investigation for an incident:
    1. Hindsight recall of past incidents
    2. Symptom & telemetry analysis
    3. Hypothesis formulation
    4. Runbook matching
    5. Mitigation recommendation
    """
    inc = db.query(IncidentDB).filter(IncidentDB.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    if inc.status == IncidentStatus.OPEN.value:
        inc.status = IncidentStatus.INVESTIGATING.value
        db.commit()

    incident_dict = {
        "id": inc.id,
        "title": inc.title,
        "service": inc.service,
        "severity": inc.severity,
        "description": inc.description,
        "symptoms": inc.symptoms or [],
        "metrics": inc.metrics or {},
        "logs": inc.logs or [],
        "deployment": inc.deployment or {},
        "created_at": inc.created_at.isoformat() if inc.created_at else None,
    }

    agent = get_incident_agent()
    result = await agent.analyze_incident(incident_dict)

    # Persist analysis in DB
    inc.analysis_result = result.model_dump()
    inc.updated_at = utc_now()
    db.commit()

    return result
