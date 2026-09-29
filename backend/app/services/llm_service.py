"""LLM service for AI-powered incident analysis."""
import json
import logging
from typing import Any, Dict, List, Optional

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class LLMService:
    """OpenAI-compatible LLM service with graceful error handling."""

    def __init__(self):
        self._client = None
        self._available = False
        self._init_client()

    def _init_client(self):
        if not settings.llm_api_key:
            logger.warning("LLM_API_KEY not set - LLM will be unavailable")
            self._available = False
            return
        try:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(
                api_key=settings.llm_api_key,
                base_url=settings.llm_base_url,
            )
            self._available = True
            logger.info(f"LLM client initialized: {settings.llm_base_url} / {settings.llm_model}")
        except ImportError:
            logger.error("openai package not installed")
            self._available = False
        except Exception as e:
            logger.error(f"LLM client init failed: {e}")
            self._available = False

    async def health_check(self) -> Dict[str, Any]:
        if not self._client or not self._available:
            return {"connected": False, "model": settings.llm_model, "message": "API key missing or client not initialized"}
        try:
            models = await self._client.models.list()
            return {"connected": True, "model": settings.llm_model, "base_url": settings.llm_base_url}
        except Exception as e:
            return {"connected": False, "model": settings.llm_model, "message": str(e)}

    async def analyze_incident(
        self,
        incident: Dict[str, Any],
        historical_memories: List[Dict[str, Any]],
        hindsight_reflection: Optional[str],
        runbooks: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Use LLM to analyze an incident with historical context.
        Returns structured analysis or degraded response.
        """
        if not self._client or not self._available:
            return self._fallback_analysis(incident, historical_memories)

        historical_section = ""
        if historical_memories:
            historical_section = "\n\nHISTORICAL MEMORIES FROM HINDSIGHT:\n"
            for i, mem in enumerate(historical_memories, 1):
                historical_section += f"{i}. {mem.get('text', '')}\n"
        else:
            historical_section = "\n\nHISTORICAL MEMORIES: None found."

        reflection_section = ""
        if hindsight_reflection:
            reflection_section = f"\n\nHINDSIGHT REFLECTION INSIGHT:\n{hindsight_reflection}"

        runbook_section = ""
        if runbooks:
            runbook_section = "\n\nAVAILABLE RUNBOOKS:\n"
            for rb in runbooks[:5]:
                runbook_section += f"- {rb.get('name', '')}: {rb.get('description', '')}\n"

        prompt = f"""You are an expert Site Reliability Engineer (SRE) analyzing an incident.

INCIDENT DETAILS:
- ID: {incident.get('id', 'unknown')}
- Title: {incident.get('title', '')}
- Service: {incident.get('service', '')}
- Severity: {incident.get('severity', '')}
- Description: {incident.get('description', '')}
- Symptoms: {', '.join(incident.get('symptoms', []))}
- Metrics: {json.dumps(incident.get('metrics', {}))}
- Recent Logs: {'; '.join(incident.get('logs', [])[:3])}
- Deployment Info: {json.dumps(incident.get('deployment', {}))}
{historical_section}
{reflection_section}
{runbook_section}

Based on the above information, provide a structured incident analysis in JSON format:

{{
  "summary": "one paragraph summary of what is likely happening",
  "hypotheses": [
    {{
      "cause": "specific root cause hypothesis",
      "confidence": 0.85,
      "evidence": ["evidence point 1", "evidence point 2"],
      "reasoning": "why you think this is the cause",
      "category": "deployment|resource|network|database|application|unknown"
    }}
  ],
  "recommended_runbooks": ["runbook name 1", "runbook name 2"],
  "recommended_actions": [
    {{
      "action": "specific action to take",
      "reason": "why this action",
      "evidence": ["supporting evidence"],
      "historical_support": "incident ID if historical incident supports this",
      "runbook": "runbook name if applicable",
      "risk": "low|medium|high",
      "expected_outcome": "what should happen after this action",
      "priority": 1
    }}
  ],
  "confidence_score": 0.75
}}

Important:
- If historical memories mention a similar incident with a resolution, heavily weight that.
- Be specific about root causes based on symptoms and metrics.
- List hypotheses in descending order of confidence.
- Only reference historical incidents if they actually appear in the memories provided.
- Do not fabricate historical references.

Respond ONLY with valid JSON, no markdown.
"""

        try:
            response = await self._client.chat.completions.create(
                model=settings.llm_model,
                messages=[
                    {"role": "system", "content": "You are an expert SRE. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=2000,
            )
            raw = response.choices[0].message.content.strip()
            # Strip markdown code block if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            parsed = json.loads(raw)
            logger.info(f"LLM analysis completed for incident {incident.get('id')}")
            return {"available": True, "analysis": parsed}
        except json.JSONDecodeError as e:
            logger.error(f"LLM returned invalid JSON: {e}")
            return self._fallback_analysis(incident, historical_memories)
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return self._fallback_analysis(incident, historical_memories)

    async def generate_postmortem_text(
        self,
        incident: Dict[str, Any],
        analysis: Optional[Dict[str, Any]],
        approval_decision: Optional[str],
    ) -> Dict[str, Any]:
        """Generate postmortem content using LLM."""
        if not self._client or not self._available:
            return {"available": False, "postmortem": None}

        prompt = f"""Generate a professional incident postmortem report for the following incident.

INCIDENT:
- ID: {incident.get('id', '')}
- Title: {incident.get('title', '')}
- Service: {incident.get('service', '')}
- Severity: {incident.get('severity', '')}
- Description: {incident.get('description', '')}
- Symptoms: {', '.join(incident.get('symptoms', []))}
- Resolution: {incident.get('resolution_summary', 'Not yet documented')}

ANALYSIS SUMMARY: {analysis.get('summary', 'No analysis available') if analysis else 'No analysis available'}
APPROVAL DECISION: {approval_decision or 'Not recorded'}

Return a JSON postmortem with this exact structure:
{{
  "incident_summary": "executive summary (2-3 sentences)",
  "impact": "business/user impact description",
  "timeline": [
    {{"timestamp": "T+0m", "event": "incident detected", "actor": "monitoring"}},
    {{"timestamp": "T+5m", "event": "investigation started", "actor": "on-call engineer"}},
    {{"timestamp": "T+15m", "event": "root cause identified", "actor": "AI agent"}},
    {{"timestamp": "T+20m", "event": "remediation approved", "actor": "operator"}},
    {{"timestamp": "T+30m", "event": "incident resolved", "actor": "system"}}
  ],
  "root_cause": "specific root cause identified",
  "contributing_factors": ["factor 1", "factor 2"],
  "resolution": "what was done to resolve it",
  "runbook_used": "runbook name or null",
  "what_worked": ["thing that worked 1", "thing that worked 2"],
  "what_failed": ["thing that failed or delayed resolution"],
  "lessons_learned": ["lesson 1", "lesson 2", "lesson 3"],
  "follow_up_actions": ["action item 1 (owner)", "action item 2 (owner)"]
}}

Respond ONLY with valid JSON.
"""
        try:
            response = await self._client.chat.completions.create(
                model=settings.llm_model,
                messages=[
                    {"role": "system", "content": "You are an expert SRE writing postmortems. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=2000,
            )
            raw = response.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            parsed = json.loads(raw)
            return {"available": True, "postmortem": parsed}
        except Exception as e:
            logger.error(f"LLM postmortem generation failed: {e}")
            return {"available": False, "postmortem": None}

    def _fallback_analysis(
        self,
        incident: Dict[str, Any],
        historical_memories: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Rule-based fallback when LLM is unavailable."""
        return {
            "available": False,
            "analysis": {
                "summary": (
                    f"LLM analysis unavailable. Incident '{incident.get('title', '')}' "
                    f"on {incident.get('service', '')} with severity {incident.get('severity', '')}. "
                    f"{'Historical memories found from Hindsight.' if historical_memories else 'No historical memory found.'} "
                    "Manual investigation required."
                ),
                "hypotheses": [],
                "recommended_runbooks": [],
                "recommended_actions": [],
                "confidence_score": 0.0,
            },
        }


_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
