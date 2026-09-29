"""Recommendation Engine: Generates concrete mitigation recommendations linked to runbooks and historical precedents."""
from typing import Any, Dict, List, Optional
import re
from app.models.recommendation import Recommendation, RecommendationSet
from app.models.analysis import Hypothesis


class RecommendationEngine:
    """
    Synthesizes hypotheses, matched runbooks, and Hindsight learnings into
    ranked recommendations with risk assessments and expected outcomes.
    """

    def generate_recommendations(
        self,
        incident: Dict[str, Any],
        hypotheses: List[Hypothesis],
        matched_runbooks: List[Dict[str, Any]],
        historical_memories: Optional[List[Dict[str, Any]]] = None,
        llm_recommendations: Optional[List[Dict[str, Any]]] = None,
    ) -> RecommendationSet:
        historical_memories = historical_memories or []
        recs: List[Recommendation] = []

        # Find historical incident ID and resolution if mentioned in memories
        hist_incident_id = None
        hist_resolution = None
        hist_runbook = None
        for mem in historical_memories:
            text = mem.get("text", "")
            id_match = re.search(r"(IR-\w+)", text)
            if id_match and not hist_incident_id:
                hist_incident_id = id_match.group(1)
            res_match = re.search(r"resolution[:\s]+([^\n\.,]+)", text, re.I)
            if res_match and not hist_resolution:
                hist_resolution = res_match.group(1).strip()
            rb_match = re.search(r"runbook[:\s]+([^\n\.,]+)", text, re.I)
            if rb_match and not hist_runbook:
                hist_runbook = rb_match.group(1).strip()

        # If LLM recommendations are provided, convert them
        if llm_recommendations:
            for i, r in enumerate(llm_recommendations, 1):
                try:
                    rec = Recommendation(
                        action=r.get("action", "Perform diagnostic investigation"),
                        reason=r.get("reason", "Remediation step based on current hypotheses"),
                        evidence=list(r.get("evidence", [])),
                        historical_support=r.get("historical_support") or hist_incident_id,
                        runbook=r.get("runbook") or (matched_runbooks[0]["name"] if matched_runbooks else None),
                        risk=r.get("risk", "medium"),
                        expected_outcome=r.get("expected_outcome", "Resolution of incident symptoms"),
                        priority=int(r.get("priority", i)),
                    )
                    recs.append(rec)
                except Exception:
                    pass

        # If no LLM recommendations or need fallback
        if not recs:
            top_hyp = hypotheses[0] if hypotheses else None
            top_rb = matched_runbooks[0] if matched_runbooks else None
            svc = incident.get("service", "service")

            # Check if there's historical precedent from Hindsight
            if hist_incident_id or historical_memories:
                action_text = f"Rollback latest {svc} deployment and restart pods"
                reason_text = (
                    f"A similar historical incident ({hist_incident_id or 'recalled in Hindsight'}) "
                    f"was resolved by rolling back deployment. {hist_resolution or ''}".strip()
                )
                recs.append(
                    Recommendation(
                        action=action_text,
                        reason=reason_text,
                        evidence=[
                            f"Corroborated by historical postmortem {hist_incident_id or 'in Hindsight'}",
                            f"Top hypothesis: {top_hyp.cause if top_hyp else 'Deployment memory leak'}",
                            f"Runbook matched: {top_rb.get('name') if top_rb else 'API Gateway Memory Leak Recovery'}",
                        ],
                        historical_support=hist_incident_id,
                        runbook=top_rb.get("name") if top_rb else (hist_runbook or "API Gateway Memory Leak Recovery"),
                        risk="medium",
                        expected_outcome=f"{svc} memory and CPU utilization stabilize to baseline; error rate drops to 0%.",
                        priority=1,
                    )
                )

                recs.append(
                    Recommendation(
                        action=f"Scale out {svc} replica count temporarily by +50%",
                        reason="Buffer client traffic while rollback is in progress to avoid 503 throttling.",
                        evidence=["High resource load active on existing nodes"],
                        historical_support=hist_incident_id,
                        runbook="High CPU Investigation",
                        risk="low",
                        expected_outcome="Immediate latency relief and traffic head-room.",
                        priority=2,
                    )
                )
            else:
                # First time incident (no Hindsight memories yet)
                if top_hyp and "memory leak" in top_hyp.cause.lower():
                    recs.append(
                        Recommendation(
                            action=f"Rollback the latest {svc} deployment",
                            reason="Telemetry shows steady memory growth since the recent software release, indicating a software memory leak.",
                            evidence=[
                                "Continuous memory escalation",
                                f"Recent deployment detected on {svc}",
                            ],
                            historical_support=None,
                            runbook=top_rb.get("name") if top_rb else "API Gateway Memory Leak Recovery",
                            risk="medium",
                            expected_outcome=f"Resource usage returns to pre-deployment baseline on {svc}.",
                            priority=1,
                        )
                    )
                elif top_hyp and "database" in top_hyp.cause.lower():
                    recs.append(
                        Recommendation(
                            action="Terminate long-running unindexed queries and recycle connection pool",
                            reason="Active pool connections are blocked by slow queries exceeding execution threshold.",
                            evidence=["Database timeout threshold exceeded", "High connection count"],
                            historical_support=None,
                            runbook=top_rb.get("name") if top_rb else "Database Timeout Recovery",
                            risk="medium",
                            expected_outcome="Connection pool availability restored immediately.",
                            priority=1,
                        )
                    )
                else:
                    recs.append(
                        Recommendation(
                            action=f"Restart unhealthy {svc} instances and inspect deployment diff",
                            reason="Mitigate immediate blast radius while inspecting recent deployment changelog.",
                            evidence=["Service health check failures", "Elevated latency"],
                            historical_support=None,
                            runbook=top_rb.get("name") if top_rb else "High CPU Investigation",
                            risk="low",
                            expected_outcome="Service recovery and diagnostic log capture.",
                            priority=1,
                        )
                    )

        # Build RecommendationSet
        primary = recs[0] if recs else None
        hist_context = (
            f"Precedent from {hist_incident_id}: previously resolved using {hist_runbook or 'recommended runbook'}."
            if hist_incident_id
            else "No historical incident precedent found. Recommendation derived from first-principles analysis."
        )

        return RecommendationSet(
            incident_id=incident.get("id", "unknown"),
            primary_recommendation=primary,
            all_recommendations=recs,
            historical_context=hist_context,
            confidence=0.92 if hist_incident_id else 0.75,
        )
