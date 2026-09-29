"""Runbooks Router: Endpoints for browsing and searching incident response runbooks."""
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException
from app.services.runbook_service import get_runbook_service

router = APIRouter(prefix="/api/runbooks", tags=["runbooks"])


@router.get("", response_model=List[Dict[str, Any]])
def list_runbooks():
    svc = get_runbook_service()
    return svc.get_all()


@router.get("/{runbook_id}", response_model=Dict[str, Any])
def get_runbook(runbook_id: str):
    svc = get_runbook_service()
    rb = svc.get_by_id(runbook_id)
    if not rb:
        raise HTTPException(status_code=404, detail=f"Runbook {runbook_id} not found")
    return rb
