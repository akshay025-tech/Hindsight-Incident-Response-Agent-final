"""Pydantic models for AI analysis results."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class EvidenceItem(BaseModel):
    description: str
    source: str = "system"
    confidence: float = 0.5


class Hypothesis(BaseModel):
    cause: str
    confidence: float  # 0.0 - 1.0
    evidence: List[str] = []
    reasoning: str
    category: str = "unknown"


class HindsightMemory(BaseModel):
    text: str
    type: Optional[str] = None
    context: Optional[str] = None
    id: Optional[str] = None
    relevance_score: Optional[float] = None


class AnalysisResult(BaseModel):
    incident_id: str
    summary: str
    historical_memory_found: bool = False
    historical_memories: List[HindsightMemory] = []
    similar_incidents: List[str] = []
    reflect_insight: Optional[str] = None
    hypotheses: List[Hypothesis] = []
    recommended_runbooks: List[str] = []
    recommended_actions: List[Dict[str, Any]] = []
    requires_human_approval: bool = True
    confidence_score: float = 0.0
    analysis_timestamp: Optional[str] = None
