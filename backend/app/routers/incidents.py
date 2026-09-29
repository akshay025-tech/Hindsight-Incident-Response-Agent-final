"""Incident Router: Endpoints for incident CRUD, simulation, and operator approvals."""
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db, IncidentDB, ApprovalDB, PostmortemDB, utc_now
from app.models.incident import (
    Incident,
    IncidentCreate,
    IncidentUpdate,
    IncidentStatus,
    Severity,
    SimulateIncidentRequest,
    ApprovalRequest,
)

router = APIRouter(prefix="/api/incidents", tags=["incidents"])


@router.get("", response_model=List[Incident])
def list_incidents(
    status_filter: Optional[str] = Query(None, alias="status"),
    service_filter: Optional[str] = Query(None, alias="service"),
    severity_filter: Optional[str] = Query(None, alias="severity"),
    search_query: Optional[str] = Query(None, alias="search"),
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(IncidentDB).outerjoin(
        PostmortemDB,
        PostmortemDB.incident_id == IncidentDB.id,
    )
    if status_filter:
        query = query.filter(IncidentDB.status == status_filter.upper())
    if service_filter:
        query = query.filter(IncidentDB.service == service_filter)
    if severity_filter:
        query = query.filter(IncidentDB.severity == severity_filter.upper())
    if search_query:
        search_term = f"%{search_query.strip()}%"
        query = query.filter(
            or_(
                IncidentDB.id.ilike(search_term),
                IncidentDB.title.ilike(search_term),
                IncidentDB.description.ilike(search_term),
                IncidentDB.service.ilike(search_term),
                IncidentDB.severity.ilike(search_term),
                IncidentDB.status.ilike(search_term),
                PostmortemDB.root_cause.ilike(search_term),
            )
        )

    incidents = query.order_by(IncidentDB.created_at.desc()).limit(limit).all()
    return [
        Incident(
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
            resolution_summary=inc.resolution_summary,
            created_at=inc.created_at,
            updated_at=inc.updated_at,
        )
        for inc in incidents
    ]


@router.get("/{incident_id}", response_model=Incident)
def get_incident(incident_id: str, db: Session = Depends(get_db)):
    inc = db.query(IncidentDB).filter(IncidentDB.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
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
        resolution_summary=inc.resolution_summary,
        created_at=inc.created_at,
        updated_at=inc.updated_at,
    )


@router.post("", response_model=Incident, status_code=status.HTTP_201_CREATED)
def create_incident(req: IncidentCreate, db: Session = Depends(get_db)):
    inc_id = f"IR-{uuid.uuid4().hex[:6].upper()}"
    new_inc = IncidentDB(
        id=inc_id,
        title=req.title,
        service=req.service,
        severity=req.severity.value,
        status=IncidentStatus.OPEN.value,
        description=req.description,
        symptoms=req.symptoms,
        metrics=req.metrics,
        logs=req.logs,
        deployment=req.deployment,
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    db.add(new_inc)
    db.commit()
    db.refresh(new_inc)
    return get_incident(inc_id, db)


@router.patch("/{incident_id}", response_model=Incident)
def update_incident(incident_id: str, req: IncidentUpdate, db: Session = Depends(get_db)):
    inc = db.query(IncidentDB).filter(IncidentDB.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    if req.title is not None:
        inc.title = req.title
    if req.severity is not None:
        inc.severity = req.severity.value
    if req.status is not None:
        inc.status = req.status.value
    if req.description is not None:
        inc.description = req.description
    if req.symptoms is not None:
        inc.symptoms = req.symptoms
    if req.metrics is not None:
        inc.metrics = req.metrics
    if req.logs is not None:
        inc.logs = req.logs
    if req.deployment is not None:
        inc.deployment = req.deployment
    if req.resolution_summary is not None:
        inc.resolution_summary = req.resolution_summary

    inc.updated_at = utc_now()
    db.commit()
    db.refresh(inc)
    return get_incident(incident_id, db)


@router.post("/simulate", response_model=Incident, status_code=status.HTTP_201_CREATED)
def simulate_incident(req: SimulateIncidentRequest, db: Session = Depends(get_db)):
    """Simulate a realistic incident based on preset types."""
    inc_type = req.incident_type.lower()
    custom_service = req.service

    simulations = {
        "high_cpu": {
            "title": "API Gateway High CPU",
            "service": custom_service or "api-gateway",
            "severity": Severity.HIGH,
            "description": "API Gateway nodes experiencing elevated CPU spikes exceeding 90% threshold.",
            "symptoms": ["CPU continuously increasing", "memory increasing", "recent deployment", "p99 latency degradation"],
            "metrics": {"cpu_percent": 94, "memory_percent": 88, "request_rate_rps": 4200, "error_rate_percent": 4.2},
            "logs": [
                "WARN [WorkerPool] thread starvation detected on worker-4",
                "WARN [GC] Full GC invocation took 1420ms",
                "ERROR [HttpIngress] upstream request timed out after 5000ms",
            ],
            "deployment": {"recent": True, "version": "v2.14.0", "timestamp": "25 minutes ago", "commit": "a8f9c1e"},
        },
        "memory_leak": {
            "title": "API Gateway Memory Leak",
            "service": custom_service or "api-gateway",
            "severity": Severity.HIGH,
            "description": "RSS memory steadily climbing post-deployment without recovery after garbage collection cycles.",
            "symptoms": ["memory increasing", "OOM kills detected", "heap dump size expanding", "recent deployment"],
            "metrics": {"cpu_percent": 89, "memory_percent": 95, "oom_kills": 3, "rss_mb": 3840},
            "logs": [
                "FATAL [Runtime] java.lang.OutOfMemoryError: Java heap space",
                "INFO [Kubelet] Container api-gateway killed by OOMKiller",
                "WARN [Router] Dropped 140 connections during pod restart",
            ],
            "deployment": {"recent": True, "version": "v2.14.0", "timestamp": "40 minutes ago", "commit": "a8f9c1e"},
        },
        "db_timeout": {
            "title": "Database Connection Pool Timeout",
            "service": custom_service or "payment-service",
            "severity": Severity.CRITICAL,
            "description": "Database queries timing out across payment-service clusters, pool slots exhausted.",
            "symptoms": ["database timeout", "connection pool exhaustion", "slow queries", "504 Gateway Timeout"],
            "metrics": {"db_connections_active": 100, "db_connections_max": 100, "query_duration_p99_ms": 6800},
            "logs": [
                "ERROR [DbPool] Connection acquisition timed out after 30000ms",
                "WARN [TransactionManager] Unable to acquire lease on Postgres primary",
                "ERROR [Checkout] Payment processing failed due to DB connection timeout",
            ],
            "deployment": {"recent": False, "version": "v1.8.2", "timestamp": "3 days ago"},
        },
        "http_5xx": {
            "title": "HTTP 5xx Error Rate Spike",
            "service": custom_service or "auth-service",
            "severity": Severity.CRITICAL,
            "description": "Sudden surge in HTTP 500 and 502 status responses following config change.",
            "symptoms": ["HTTP 5xx spike", "502 Bad Gateway", "auth token validation failures", "recent deployment"],
            "metrics": {"error_rate_percent": 34.5, "status_500_count": 1280, "p99_latency_ms": 3200},
            "logs": [
                "ERROR [TokenValidator] JWKS public key endpoint unreachable",
                "ERROR [AuthHandler] NullPointerException during claim verification",
                "WARN [Proxy] Upstream auth-service returned status 502",
            ],
            "deployment": {"recent": True, "version": "v3.1.0", "timestamp": "12 minutes ago"},
        },
        "slow_query": {
            "title": "Unindexed Slow Query Saturation",
            "service": custom_service or "user-service",
            "severity": Severity.MEDIUM,
            "description": "Sequential table scan on user_activity table causing replication lag and worker stalls.",
            "symptoms": ["slow query", "database load", "elevated p95 latency"],
            "metrics": {"query_duration_p99_ms": 4500, "db_cpu_percent": 86, "replication_lag_seconds": 45},
            "logs": [
                "WARN [PgStat] Sequential scan detected on user_activity (14M rows)",
                "INFO [SlowLog] Query execution time: 4210ms SELECT * FROM user_activity WHERE tenant_id = ...",
            ],
            "deployment": {"recent": False, "version": "v4.0.1"},
        },
        "bad_deployment": {
            "title": "Broken Release CrashLoopBackOff",
            "service": custom_service or "order-service",
            "severity": Severity.CRITICAL,
            "description": "New service revision failing liveness probe immediately upon startup.",
            "symptoms": ["CrashLoopBackOff", "bad deployment", "liveness probe failure", "pod restarts"],
            "metrics": {"restarts_15m": 12, "healthy_replicas": 0, "desired_replicas": 4},
            "logs": [
                "FATAL [Main] Missing required environment variable SECRET_KEY_BASE",
                "INFO [Kubelet] Container order-service failed liveness probe, restarting",
            ],
            "deployment": {"recent": True, "version": "v1.9.0", "timestamp": "5 minutes ago"},
        },
    }

    sim = simulations.get(inc_type, simulations["high_cpu"])
    inc_id = f"IR-{uuid.uuid4().hex[:6].upper()}"

    new_inc = IncidentDB(
        id=inc_id,
        title=sim["title"],
        service=sim["service"],
        severity=req.severity.value if req.severity else sim["severity"].value,
        status=IncidentStatus.OPEN.value,
        description=sim["description"],
        symptoms=sim["symptoms"],
        metrics=sim["metrics"],
        logs=sim["logs"],
        deployment=sim["deployment"],
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    db.add(new_inc)
    db.commit()
    db.refresh(new_inc)
    return get_incident(inc_id, db)


@router.post("/{incident_id}/approve")
def approve_action(
    incident_id: str,
    req: ApprovalRequest,
    db: Session = Depends(get_db),
):
    """Operator approval of recommended remediation action."""
    inc = db.query(IncidentDB).filter(IncidentDB.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    approval_id = f"APP-{uuid.uuid4().hex[:6].upper()}"
    analysis = inc.analysis_result or {}
    recs = analysis.get("recommended_actions") or []
    primary_rec = recs[0] if recs else {}

    approval = ApprovalDB(
        id=approval_id,
        incident_id=incident_id,
        decision="approve",
        operator_comment=req.operator_comment or "Action approved by operator via Incident Response Command Center",
        operator_id=req.operator_id or "operator",
        recommendation_snapshot=primary_rec,
        created_at=utc_now(),
    )
    db.add(approval)

    # Transition incident to MITIGATED / RESOLVED
    inc.status = IncidentStatus.MITIGATED.value
    res_action = primary_rec.get("action", "Remediation action executed successfully")
    inc.resolution_summary = f"Operator approved and applied: {res_action}"
    inc.updated_at = utc_now()

    db.commit()
    return {
        "status": "approved",
        "approval_id": approval_id,
        "incident_id": incident_id,
        "executed_action": res_action,
        "incident_status": inc.status,
        "message": "Mitigation applied (Simulated Execution). Service stabilizing.",
    }


@router.post("/{incident_id}/reject")
def reject_action(
    incident_id: str,
    req: ApprovalRequest,
    db: Session = Depends(get_db),
):
    """Operator rejection of recommended remediation action."""
    inc = db.query(IncidentDB).filter(IncidentDB.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    approval_id = f"REJ-{uuid.uuid4().hex[:6].upper()}"
    approval = ApprovalDB(
        id=approval_id,
        incident_id=incident_id,
        decision="reject",
        operator_comment=req.operator_comment or "Action rejected by operator",
        operator_id=req.operator_id or "operator",
        recommendation_snapshot=None,
        created_at=utc_now(),
    )
    db.add(approval)

    inc.status = IncidentStatus.INVESTIGATING.value
    inc.updated_at = utc_now()
    db.commit()

    return {
        "status": "rejected",
        "approval_id": approval_id,
        "incident_id": incident_id,
        "incident_status": inc.status,
        "message": "Recommendation rejected by operator. Escalated for manual triage.",
    }
