"""Postmortem Service: Generates comprehensive incident postmortems and retains operational learning in Hindsight."""
import io
import json
import logging
import textwrap
from datetime import datetime
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from sqlalchemy.orm import Session
from app.models.postmortem import Postmortem, PostmortemCreate, TimelineEntry
from app.database import PostmortemDB, IncidentDB, utc_now
from app.services.hindsight_service import get_hindsight_service
from app.services.llm_service import get_llm_service

logger = logging.getLogger(__name__)


class PostmortemService:
    def __init__(self):
        self.hindsight = get_hindsight_service()
        self.llm = get_llm_service()

    def get_by_incident_id(self, db: Session, incident_id: str) -> Optional[Postmortem]:
        db_pm = db.query(PostmortemDB).filter(PostmortemDB.incident_id == incident_id).first()
        if not db_pm:
            return None
        return Postmortem(
            incident_id=db_pm.incident_id,
            incident_summary=db_pm.incident_summary,
            impact=db_pm.impact,
            timeline=[TimelineEntry(**t) if isinstance(t, dict) else t for t in (db_pm.timeline or [])],
            root_cause=db_pm.root_cause,
            contributing_factors=db_pm.contributing_factors or [],
            resolution=db_pm.resolution,
            runbook_used=db_pm.runbook_used,
            what_worked=db_pm.what_worked or [],
            what_failed=db_pm.what_failed or [],
            lessons_learned=db_pm.lessons_learned or [],
            follow_up_actions=db_pm.follow_up_actions or [],
            operator_feedback=db_pm.operator_feedback,
            retained_in_hindsight=db_pm.retained_in_hindsight,
            hindsight_retention_id=db_pm.hindsight_retention_id,
            created_at=db_pm.created_at,
            updated_at=db_pm.updated_at,
        )

    def build_pdf(self, db: Session, incident_id: str) -> Optional[bytes]:
        incident = db.query(IncidentDB).filter(IncidentDB.id == incident_id).first()
        postmortem = self.get_by_incident_id(db, incident_id)
        if not incident or not postmortem:
            return None

        buffer = io.BytesIO()
        report = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        margin = 48
        y = height - margin

        def heading(text, size=16):
            nonlocal y
            if y < 72:
                report.showPage()
                y = height - margin
            report.setFillColor(colors.HexColor("#4f46e5"))
            report.setFont("Helvetica-Bold", size)
            report.drawString(margin, y, text)
            y -= size + 8

        def body(text, size=10):
            nonlocal y
            report.setFillColor(colors.HexColor("#20232a"))
            report.setFont("Helvetica", size)
            for line in textwrap.wrap(str(text or "-"), width=96) or ["-"]:
                if y < 54:
                    report.showPage()
                    y = height - margin
                    report.setFont("Helvetica", size)
                report.drawString(margin, y, line)
                y -= size + 4
            y -= 4

        report.setTitle(f"Postmortem {incident.id}")
        report.setAuthor("Incident Response Agent")
        heading("INCIDENT RESPONSE AGENT", 20)
        heading("POSTMORTEM REPORT", 16)
        body(f"Incident ID: {incident.id}")
        body(f"Incident Title: {incident.title}")
        body(f"Severity: {incident.severity}")
        body(f"Service: {incident.service}")
        body(f"Created / Detected: {incident.created_at}")
        body(f"Resolved / Last Updated: {incident.updated_at}")
        body(f"Generated At: {utc_now()}")

        sections = [
            ("Executive Summary", postmortem.incident_summary),
            ("Impact", postmortem.impact),
            ("Timeline", "\n".join(f"{item.timestamp} - {item.event} ({item.actor or 'System'})" for item in postmortem.timeline)),
            ("Root Cause", postmortem.root_cause),
            ("Contributing Factors", "\n".join(postmortem.contributing_factors)),
            ("Resolution", postmortem.resolution),
            ("Runbook Used", postmortem.runbook_used),
            ("What Worked", "\n".join(postmortem.what_worked)),
            ("What Failed", "\n".join(postmortem.what_failed)),
            ("Lessons Learned", "\n".join(postmortem.lessons_learned)),
            ("Follow-up Actions", "\n".join(postmortem.follow_up_actions)),
            ("AI Analysis", json.dumps(incident.analysis_result or {}, indent=2, default=str)),
        ]
        for title, value in sections:
            heading(title, 12)
            body(value)

        report.save()
        return buffer.getvalue()

    async def generate_postmortem(
        self,
        db: Session,
        incident_id: str,
        operator_feedback: Optional[str] = None,
        custom_data: Optional[Dict[str, Any]] = None,
    ) -> Postmortem:
        """
        Generate postmortem for an incident using LLM with deterministic fallback,
        save to SQLite, and automatically retain knowledge in Hindsight.
        """
        inc_db = db.query(IncidentDB).filter(IncidentDB.id == incident_id).first()
        if not inc_db:
            raise ValueError(f"Incident {incident_id} not found")

        incident_dict = {
            "id": inc_db.id,
            "title": inc_db.title,
            "service": inc_db.service,
            "severity": inc_db.severity,
            "description": inc_db.description,
            "symptoms": inc_db.symptoms or [],
            "resolution_summary": inc_db.resolution_summary,
        }

        analysis_data = inc_db.analysis_result or {}

        # If custom data provided by user in API call, use it
        if custom_data:
            summary = custom_data.get("incident_summary") or f"Postmortem for {inc_db.title} on {inc_db.service}"
            impact = custom_data.get("impact") or f"Severity {inc_db.severity} service disruption on {inc_db.service}"
            root_cause = custom_data.get("root_cause") or "Identified operational anomaly"
            resolution = custom_data.get("resolution") or (inc_db.resolution_summary or "Remediated by on-call engineer")
            runbook = custom_data.get("runbook_used")
            timeline = [TimelineEntry(**t) if isinstance(t, dict) else t for t in custom_data.get("timeline", [])]
            contributing = custom_data.get("contributing_factors", [])
            what_worked = custom_data.get("what_worked", [])
            what_failed = custom_data.get("what_failed", [])
            lessons = custom_data.get("lessons_learned", [])
            follow_ups = custom_data.get("follow_up_actions", [])
        else:
            # Try LLM generation
            llm_res = await self.llm.generate_postmortem_text(
                incident=incident_dict,
                analysis=analysis_data,
                approval_decision="Approved",
            )

            if llm_res.get("available") and llm_res.get("postmortem"):
                pm_data = llm_res["postmortem"]
                summary = pm_data.get("incident_summary", f"Incident {inc_db.id} on {inc_db.service}")
                impact = pm_data.get("impact", f"Degraded response times on {inc_db.service}")
                root_cause = pm_data.get("root_cause", "Operational failure")
                resolution = pm_data.get("resolution", inc_db.resolution_summary or "Rolled back deployment")
                runbook = pm_data.get("runbook_used")
                timeline = [TimelineEntry(**t) for t in pm_data.get("timeline", [])]
                contributing = pm_data.get("contributing_factors", [])
                what_worked = pm_data.get("what_worked", [])
                what_failed = pm_data.get("what_failed", [])
                lessons = pm_data.get("lessons_learned", [])
                follow_ups = pm_data.get("follow_up_actions", [])
            else:
                # Deterministic high-quality postmortem for demo scenarios
                top_hyp = (analysis_data.get("hypotheses") or [{}])[0]
                hyp_cause = top_hyp.get("cause", "Deployment-related memory leak")
                rb_list = analysis_data.get("recommended_runbooks") or ["API Gateway Memory Leak Recovery"]
                runbook = rb_list[0] if rb_list else "API Gateway Memory Leak Recovery"

                summary = (
                    f"On {utc_now().strftime('%Y-%m-%d')}, {inc_db.service} experienced {inc_db.title}. "
                    f"AI automated investigation correlated symptoms with {hyp_cause}. "
                    "Remediation was executed following operator approval, successfully restoring service health."
                )
                impact = f"Service degradation on {inc_db.service}; latency elevated across API endpoints during incident duration."
                root_cause = hyp_cause
                resolution = inc_db.resolution_summary or "Rollback deployment + restart service"
                contributing = [
                    "Recent service deployment with uncapped object allocations",
                    "Insufficient automated soak-testing before production release",
                ]
                what_worked = [
                    f"Rapid diagnosis via AI incident response agent",
                    f"Application of runbook: '{runbook}'",
                    "Human-in-the-loop review provided prompt approval",
                ]
                what_failed = [
                    "Canary deployment analysis did not catch the steady memory progression early enough",
                ]
                lessons = [
                    "Long-term memory retention enables instant recognition of recurrent regression patterns",
                    "Add automated load tests checking for RSS memory slope prior to production rollouts",
                    f"Keep runbook '{runbook}' updated with step-by-step verification commands",
                ]
                follow_ups = [
                    "Implement heap dump profiling in staging pipeline (Owner: SRE)",
                    "Audit connection pool limits across API gateway workers (Owner: DevOps)",
                ]
                timeline = [
                    TimelineEntry(timestamp="T+0m", event=f"Alert triggered: {inc_db.title}", actor="Monitoring"),
                    TimelineEntry(timestamp="T+2m", event="Agent initiated investigation & Hindsight query", actor="AI Agent"),
                    TimelineEntry(timestamp="T+5m", event=f"Root cause hypothesis generated: {root_cause}", actor="AI Agent"),
                    TimelineEntry(timestamp="T+7m", event="Operator reviewed and approved recommended runbook", actor="Operator"),
                    TimelineEntry(timestamp="T+12m", event=f"Remediation applied: {resolution}", actor="Operator"),
                    TimelineEntry(timestamp="T+15m", event="Metrics stabilized to baseline; incident marked RESOLVED", actor="System"),
                ]

        # Step 2: Retain learning into Hindsight
        retention_content = (
            f"INCIDENT POSTMORTEM {inc_db.id}:\n"
            f"Service: {inc_db.service}\n"
            f"Issue: {inc_db.title}\n"
            f"Symptoms: {', '.join(inc_db.symptoms or [])}\n"
            f"Root cause: {root_cause}\n"
            f"Resolution: {resolution}\n"
            f"Runbook: {runbook or 'API Gateway Memory Leak Recovery'}\n"
            f"What worked: {'; '.join(what_worked)}\n"
            f"Lessons learned: {'; '.join(lessons)}"
        )

        hindsight_res = await self.hindsight.retain_incident_learning(
            incident_id=inc_db.id,
            content=retention_content,
            context=f"Postmortem learning for {inc_db.service}",
            metadata={
                "incident_id": inc_db.id,
                "service": inc_db.service,
                "root_cause": root_cause,
                "runbook": runbook,
                "severity": inc_db.severity,
            },
        )

        retained = hindsight_res.get("retained", False)
        retention_id = inc_db.id if retained else None

        # Save or update in DB
        db_pm = db.query(PostmortemDB).filter(PostmortemDB.incident_id == incident_id).first()
        timeline_json = [t.model_dump() for t in timeline]

        if db_pm:
            db_pm.incident_summary = summary
            db_pm.impact = impact
            db_pm.timeline = timeline_json
            db_pm.root_cause = root_cause
            db_pm.contributing_factors = contributing
            db_pm.resolution = resolution
            db_pm.runbook_used = runbook
            db_pm.what_worked = what_worked
            db_pm.what_failed = what_failed
            db_pm.lessons_learned = lessons
            db_pm.follow_up_actions = follow_ups
            db_pm.operator_feedback = operator_feedback
            db_pm.retained_in_hindsight = retained
            db_pm.hindsight_retention_id = retention_id
            db_pm.updated_at = utc_now()
        else:
            db_pm = PostmortemDB(
                incident_id=inc_db.id,
                incident_summary=summary,
                impact=impact,
                timeline=timeline_json,
                root_cause=root_cause,
                contributing_factors=contributing,
                resolution=resolution,
                runbook_used=runbook,
                what_worked=what_worked,
                what_failed=what_failed,
                lessons_learned=lessons,
                follow_up_actions=follow_ups,
                operator_feedback=operator_feedback,
                retained_in_hindsight=retained,
                hindsight_retention_id=retention_id,
            )
            db.add(db_pm)

        db.commit()
        db.refresh(db_pm)

        return self.get_by_incident_id(db, incident_id)


_postmortem_service: Optional[PostmortemService] = None


def get_postmortem_service() -> PostmortemService:
    global _postmortem_service
    if _postmortem_service is None:
        _postmortem_service = PostmortemService()
    return _postmortem_service
