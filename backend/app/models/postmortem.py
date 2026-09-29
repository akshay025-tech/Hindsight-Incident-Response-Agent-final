"""Pydantic models for postmortems."""
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict


class TimelineEntry(BaseModel):
    timestamp: str
    event: str
    actor: Optional[str] = None


class PostmortemCreate(BaseModel):
    incident_summary: str
    impact: str
    timeline: List[TimelineEntry] = []
    root_cause: str
    contributing_factors: List[str] = []
    resolution: str
    runbook_used: Optional[str] = None
    what_worked: List[str] = []
    what_failed: List[str] = []
    lessons_learned: List[str] = []
    follow_up_actions: List[str] = []
    operator_feedback: Optional[str] = None


class Postmortem(PostmortemCreate):
    incident_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    retained_in_hindsight: bool = False
    hindsight_retention_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

