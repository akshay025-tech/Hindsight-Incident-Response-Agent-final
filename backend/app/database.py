from datetime import datetime, timezone
from typing import Optional
import json

from sqlalchemy import create_engine, Column, String, DateTime, Text, Boolean, JSON
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from app.config import get_settings


def utc_now() -> datetime:
    """Return timezone-naive UTC datetime compatible with SQLite."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


settings = get_settings()

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class IncidentDB(Base):
    __tablename__ = "incidents"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    service = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    status = Column(String, nullable=False, default="OPEN")
    description = Column(Text, nullable=False)
    symptoms = Column(JSON, default=[])
    metrics = Column(JSON, default={})
    logs = Column(JSON, default=[])
    deployment = Column(JSON, default={})
    resolution_summary = Column(Text, nullable=True)
    analysis_result = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)


class ApprovalDB(Base):
    __tablename__ = "approvals"

    id = Column(String, primary_key=True, index=True)
    incident_id = Column(String, nullable=False, index=True)
    decision = Column(String, nullable=False)  # approve / reject
    operator_comment = Column(Text, nullable=True)
    operator_id = Column(String, nullable=True)
    recommendation_snapshot = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utc_now)


class PostmortemDB(Base):
    __tablename__ = "postmortems"

    incident_id = Column(String, primary_key=True, index=True)
    incident_summary = Column(Text, nullable=False)
    impact = Column(Text, nullable=False)
    timeline = Column(JSON, default=[])
    root_cause = Column(Text, nullable=False)
    contributing_factors = Column(JSON, default=[])
    resolution = Column(Text, nullable=False)
    runbook_used = Column(String, nullable=True)
    what_worked = Column(JSON, default=[])
    what_failed = Column(JSON, default=[])
    lessons_learned = Column(JSON, default=[])
    follow_up_actions = Column(JSON, default=[])
    operator_feedback = Column(Text, nullable=True)
    retained_in_hindsight = Column(Boolean, default=False)
    hindsight_retention_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)


def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
