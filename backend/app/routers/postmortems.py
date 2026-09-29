"""Postmortems Router: Endpoints for generating, inspecting, and retaining incident postmortems."""
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db, IncidentDB
from app.models.incident import IncidentStatus
from app.models.postmortem import Postmortem, PostmortemCreate
from app.services.postmortem_service import get_postmortem_service

router = APIRouter(prefix="/api/postmortems", tags=["postmortems"])


class GeneratePostmortemRequest(BaseModel):
    operator_feedback: Optional[str] = None
    custom_data: Optional[Dict[str, Any]] = None


@router.get("/{incident_id}/download")
def download_postmortem_endpoint(incident_id: str, db: Session = Depends(get_db)):
    """Download the stored postmortem as a PDF generated from backend data."""
    pdf_bytes = get_postmortem_service().build_pdf(db, incident_id)
    if not pdf_bytes:
        raise HTTPException(status_code=404, detail=f"Postmortem for incident {incident_id} not found")
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="postmortem-{incident_id}.pdf"'},
    )


@router.get("/{incident_id}", response_model=Postmortem)
def get_postmortem_endpoint(incident_id: str, db: Session = Depends(get_db)):
    svc = get_postmortem_service()
    pm = svc.get_by_incident_id(db, incident_id)
    if not pm:
        raise HTTPException(status_code=404, detail=f"Postmortem for incident {incident_id} not found")
    return pm


@router.post("/{incident_id}", response_model=Postmortem, status_code=status.HTTP_201_CREATED)
async def generate_postmortem_endpoint(
    incident_id: str,
    req: Optional[GeneratePostmortemRequest] = None,
    db: Session = Depends(get_db),
):
    """
    Generate incident postmortem:
    1. Compiles timeline, root cause, resolution, lessons learned
    2. Retains operational learning into Hindsight
    3. Updates incident status to RESOLVED
    """
    svc = get_postmortem_service()
    try:
        feedback = req.operator_feedback if req else None
        custom = req.custom_data if req else None
        pm = await svc.generate_postmortem(
            db=db,
            incident_id=incident_id,
            operator_feedback=feedback,
            custom_data=custom,
        )

        # Mark incident as RESOLVED
        inc = db.query(IncidentDB).filter(IncidentDB.id == incident_id).first()
        if inc:
            inc.status = IncidentStatus.RESOLVED.value
            db.commit()

        return pm
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate postmortem: {e}")


@router.put("/{incident_id}", response_model=Postmortem)
async def update_postmortem_endpoint(
    incident_id: str,
    req: PostmortemCreate,
    db: Session = Depends(get_db),
):
    """Update postmortem details and re-retain in Hindsight."""
    svc = get_postmortem_service()
    try:
        pm = await svc.generate_postmortem(
            db=db,
            incident_id=incident_id,
            operator_feedback=req.operator_feedback,
            custom_data=req.model_dump(),
        )
        return pm
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
