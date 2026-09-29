"""Pydantic models for incidents."""
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict
import uuid


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IncidentStatus(str, Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    MITIGATED = "MITIGATED"
    RESOLVED = "RESOLVED"


class IncidentCreate(BaseModel):
    title: str
    service: str
    severity: Severity
    description: str
    symptoms: List[str] = []
    metrics: Dict[str, Any] = {}
    logs: List[str] = []
    deployment: Dict[str, Any] = {}


class IncidentUpdate(BaseModel):
    title: Optional[str] = None
    severity: Optional[Severity] = None
    status: Optional[IncidentStatus] = None
    description: Optional[str] = None
    symptoms: Optional[List[str]] = None
    metrics: Optional[Dict[str, Any]] = None
    logs: Optional[List[str]] = None
    deployment: Optional[Dict[str, Any]] = None
    resolution_summary: Optional[str] = None


class Incident(BaseModel):
    id: str = Field(default_factory=lambda: f"IR-{uuid.uuid4().hex[:6].upper()}")
    title: str
    service: str
    severity: Severity
    status: IncidentStatus = IncidentStatus.OPEN
    description: str
    symptoms: List[str] = []
    metrics: Dict[str, Any] = {}
    logs: List[str] = []
    deployment: Dict[str, Any] = {}
    resolution_summary: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(from_attributes=True)


class SimulateIncidentRequest(BaseModel):
    incident_type: str  # "high_cpu", "db_timeout", "http_5xx", "memory_leak", "slow_query", "bad_deployment"
    service: Optional[str] = None
    severity: Optional[Severity] = None


class ApprovalRequest(BaseModel):
    decision: str = "approve"  # "approve" or "reject"
    operator_comment: Optional[str] = None
    operator_id: Optional[str] = "operator"
