"""Pydantic models for recommendations."""
from typing import List, Optional
from pydantic import BaseModel


class Recommendation(BaseModel):
    action: str
    reason: str
    evidence: List[str] = []
    historical_support: Optional[str] = None  # incident ID that supports this
    runbook: Optional[str] = None
    risk: str = "medium"  # low, medium, high
    expected_outcome: str
    priority: int = 1  # 1 = highest


class RecommendationSet(BaseModel):
    incident_id: str
    primary_recommendation: Optional[Recommendation] = None
    all_recommendations: List[Recommendation] = []
    historical_context: Optional[str] = None
    confidence: float = 0.0
