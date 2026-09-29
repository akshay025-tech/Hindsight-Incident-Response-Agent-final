"""Simulation Router: Dedicated endpoints to drive the hackathon demonstration flow."""
from datetime import datetime
from typing import Any, Dict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db, IncidentDB, ApprovalDB, PostmortemDB, utc_now
from app.models.incident import Incident, Severity, IncidentStatus

router = APIRouter(prefix="/api/simulation", tags=["simulation"])


@router.post("/demo-part1", response_model=Incident)
def create_demo_part1_incident(db: Session = Depends(get_db)):
    """
    DEMO PART 1:
    Create IR-001 on api-gateway with High CPU & Memory Leak symptoms.
    Hindsight initially has no memory of this incident.
    """
    # Check if IR-001 exists; delete if resetting
    existing = db.query(IncidentDB).filter(IncidentDB.id == "IR-001").first()
    if existing:
        db.delete(existing)
        db.query(ApprovalDB).filter(ApprovalDB.incident_id == "IR-001").delete()
        db.query(PostmortemDB).filter(PostmortemDB.incident_id == "IR-001").delete()
        db.commit()

    inc = IncidentDB(
        id="IR-001",
        title="High CPU & Memory Degradation",
        service="api-gateway",
        severity=Severity.HIGH.value,
        status=IncidentStatus.OPEN.value,
        description="API Gateway service experiencing elevated CPU (94%) and uncollected memory accumulation following rollout of v2.14.0.",
        symptoms=[
            "CPU continuously increasing",
            "memory increasing",
            "recent deployment",
            "p99 latency 2400ms",
        ],
        metrics={
            "cpu_percent": 94,
            "memory_percent": 88,
            "request_rate_rps": 4500,
            "error_rate_percent": 3.8,
            "active_connections": 1420,
        },
        logs=[
            "WARN [WorkerPool] thread pool saturation detected on worker-6",
            "WARN [GC] Long GC pause observed: 1280ms",
            "ERROR [Ingress] upstream healthcheck timeout after 3000ms",
        ],
        deployment={
            "recent": True,
            "version": "v2.14.0",
            "timestamp": "30 minutes ago",
            "author": "release-bot",
            "commit": "a8f9c1e",
        },
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    db.add(inc)
    db.commit()
    db.refresh(inc)

    return Incident(
        id=inc.id,
        title=inc.title,
        service=inc.service,
        severity=Severity(inc.severity),
        status=IncidentStatus(inc.status),
        description=inc.description,
        symptoms=inc.symptoms or [],
        metrics=inc.metrics or {},
        logs=inc.logs or [],
        deployment=inc.deployment or {},
        created_at=inc.created_at,
        updated_at=inc.updated_at,
    )


@router.post("/demo-part2", response_model=Incident)
def create_demo_part2_incident(db: Session = Depends(get_db)):
    """
    DEMO PART 2:
    Create IR-002 on api-gateway with similar High CPU & Memory Leak symptoms.
    When analyzed, Hindsight RECALLS IR-001 and provides historical recommendations!
    """
    existing = db.query(IncidentDB).filter(IncidentDB.id == "IR-002").first()
    if existing:
        db.delete(existing)
        db.query(ApprovalDB).filter(ApprovalDB.incident_id == "IR-002").delete()
        db.query(PostmortemDB).filter(PostmortemDB.incident_id == "IR-002").delete()
        db.commit()

    inc = IncidentDB(
        id="IR-002",
        title="High CPU & Memory Exhaustion",
        service="api-gateway",
        severity=Severity.HIGH.value,
        status=IncidentStatus.OPEN.value,
        description="API Gateway alerting with sustained 91% CPU and expanding memory footprint post-deployment of v2.15.1.",
        symptoms=[
            "CPU increasing",
            "memory increasing",
            "recent deployment",
            "worker saturation",
        ],
        metrics={
            "cpu_percent": 91,
            "memory_percent": 86,
            "request_rate_rps": 4350,
            "error_rate_percent": 3.1,
            "active_connections": 1390,
        },
        logs=[
            "WARN [WorkerPool] thread queue backlog exceeding 400 jobs",
            "WARN [GC] GC overhead limit warning",
            "ERROR [Health] liveness probe slow response: 2800ms",
        ],
        deployment={
            "recent": True,
            "version": "v2.15.1",
            "timestamp": "15 minutes ago",
            "author": "release-bot",
            "commit": "c4d7e2b",
        },
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    db.add(inc)
    db.commit()
    db.refresh(inc)

    return Incident(
        id=inc.id,
        title=inc.title,
        service=inc.service,
        severity=Severity(inc.severity),
        status=IncidentStatus(inc.status),
        description=inc.description,
        symptoms=inc.symptoms or [],
        metrics=inc.metrics or {},
        logs=inc.logs or [],
        deployment=inc.deployment or {},
        created_at=inc.created_at,
        updated_at=inc.updated_at,
    )


@router.post("/reset")
def reset_simulation(db: Session = Depends(get_db)):
    """Reset demo incidents and postmortems to restart fresh."""
    db.query(ApprovalDB).delete()
    db.query(PostmortemDB).delete()
    db.query(IncidentDB).delete()
    db.commit()
    return {"status": "reset", "message": "All demo incident data wiped. Ready for fresh test run."}
