"""Incident Agent: Orchestrates investigation, Hindsight recall, hypothesis generation, runbook matching, and recommendations."""
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import re

from app.models.analysis import AnalysisResult, HindsightMemory
from app.services.hindsight_service import get_hindsight_service
from app.services.llm_service import get_llm_service
from app.services.runbook_service import get_runbook_service
from app.agents.hypothesis_engine import HypothesisEngine
from app.agents.recommendation_engine import RecommendationEngine

logger = logging.getLogger(__name__)


class IncidentAgent:
    """
    Main autonomous incident response orchestrator:
    1. Incident validation
    2. Hindsight recall & reflect
    3. LLM / rule reasoning
    4. Hypothesis formulation
    5. Runbook matching (prioritizing historically proven runbooks)
    6. Recommendation generation with human-in-the-loop safeguards
    """

    def __init__(self):
        self.hindsight = get_hindsight_service()
        self.llm = get_llm_service()
        self.runbooks = get_runbook_service()
        self.hypothesis_engine = HypothesisEngine()
        self.recommendation_engine = RecommendationEngine()

    async def analyze_incident(self, incident: Dict[str, Any]) -> AnalysisResult:
        incident_id = incident.get("id", "UNKNOWN")
        service = incident.get("service", "")
        title = incident.get("title", "")
        symptoms = incident.get("symptoms", [])

        logger.info(f"Agent starting analysis for incident {incident_id} ({service})")

        # Step 1: Recall similar historical incidents from Hindsight
        recall_query = f"{service} {title} {' '.join(symptoms)} incident root cause resolution runbook"
        recall_resp = await self.hindsight.recall_similar_incidents(recall_query)

        raw_memories = recall_resp.get("memories", [])
        historical_memories: List[HindsightMemory] = []
        similar_incident_ids: List[str] = []

        for m in raw_memories:
            text = m.get("text", "")
            historical_memories.append(
                HindsightMemory(
                    text=text,
                    type=m.get("type"),
                    context=m.get("context"),
                    id=m.get("id"),
                    relevance_score=m.get("relevance_score", 0.85),
                )
            )
            # Extract incident IDs like IR-001, IR-XYZ
            found_ids = re.findall(r"(IR-\w+)", text)
            for fid in found_ids:
                if fid != incident_id and fid not in similar_incident_ids:
                    similar_incident_ids.append(fid)

        has_memories = len(historical_memories) > 0

        # Step 2: Hindsight Reflect if historical memories exist
        reflect_insight: Optional[str] = None
        if has_memories:
            reflect_resp = await self.hindsight.reflect_on_incidents(
                query=f"What common failure modes and proven remediations apply to {service} with {title}?",
                context=f"Current incident symptoms: {', '.join(symptoms)}",
            )
            reflect_insight = reflect_resp.get("text")

        # Step 3: Extract historical runbooks to boost in matching
        historical_runbook_names: List[str] = []
        for mem in historical_memories:
            text = mem.text
            rb_match = re.search(r"runbook[:\s]+([^\n\.,]+)", text, re.I)
            if rb_match:
                historical_runbook_names.append(rb_match.group(1).strip())

        # Step 4: Run LLM analysis if available
        available_runbooks = self.runbooks.get_all()
        llm_result = await self.llm.analyze_incident(
            incident=incident,
            historical_memories=[m.model_dump() for m in historical_memories],
            hindsight_reflection=reflect_insight,
            runbooks=available_runbooks,
        )

        llm_analysis_data = llm_result.get("analysis", {}) if llm_result.get("available") else None
        llm_hypotheses = llm_analysis_data.get("hypotheses") if llm_analysis_data else None
        llm_recs = llm_analysis_data.get("recommended_actions") if llm_analysis_data else None

        # Step 5: Formulate Hypotheses via HypothesisEngine
        hypotheses = self.hypothesis_engine.generate_hypotheses(
            incident=incident,
            historical_memories=[m.model_dump() for m in historical_memories],
            llm_hypotheses=llm_hypotheses,
        )

        hypothesis_causes = [h.cause for h in hypotheses]

        # Step 6: Match Runbooks with historical preference
        matched_runbooks = self.runbooks.match_runbooks(
            service=service,
            symptoms=symptoms,
            hypotheses=hypothesis_causes,
            historical_runbooks=historical_runbook_names,
        )
        matched_rb_names = [rb.get("name", "") for rb in matched_runbooks]

        # Step 7: Generate Recommendations via RecommendationEngine
        rec_set = self.recommendation_engine.generate_recommendations(
            incident=incident,
            hypotheses=hypotheses,
            matched_runbooks=matched_runbooks,
            historical_memories=[m.model_dump() for m in historical_memories],
            llm_recommendations=llm_recs,
        )

        # Step 8: Build Summary
        if has_memories:
            ref_str = f" Historical incident(s) {', '.join(similar_incident_ids)} were recalled from Hindsight memory bank." if similar_incident_ids else " Relevant historical incidents were recalled from Hindsight memory bank."
            summary = (
                f"Investigation complete for {incident_id} on {service}.{ref_str} "
                f"Root cause hypothesis: '{hypotheses[0].cause if hypotheses else 'Unknown'}' "
                f"(confidence: {int((hypotheses[0].confidence if hypotheses else 0.8) * 100)}%). "
                f"Mitigation runbook '{matched_rb_names[0] if matched_rb_names else 'Standard Procedure'}' ready for operator approval."
            )
        else:
            summary = (
                f"Initial investigation complete for {incident_id} on {service}. No historical precedent found in Hindsight memory bank. "
                f"First-principles analysis indicates '{hypotheses[0].cause if hypotheses else 'Resource exhaustion'}' "
                f"(confidence: {int((hypotheses[0].confidence if hypotheses else 0.7) * 100)}%). "
                f"Recommended action '{rec_set.primary_recommendation.action if rec_set.primary_recommendation else 'Diagnostics'}' requires human review."
            )

        recommended_actions_dicts = [r.model_dump() for r in rec_set.all_recommendations]

        return AnalysisResult(
            incident_id=incident_id,
            summary=summary,
            historical_memory_found=has_memories,
            historical_memories=historical_memories,
            similar_incidents=similar_incident_ids,
            reflect_insight=reflect_insight,
            hypotheses=hypotheses,
            recommended_runbooks=matched_rb_names,
            recommended_actions=recommended_actions_dicts,
            requires_human_approval=True,
            confidence_score=rec_set.confidence,
            analysis_timestamp=datetime.now(timezone.utc).isoformat(),
        )


_incident_agent: Optional[IncidentAgent] = None


def get_incident_agent() -> IncidentAgent:
    global _incident_agent
    if _incident_agent is None:
        _incident_agent = IncidentAgent()
    return _incident_agent
