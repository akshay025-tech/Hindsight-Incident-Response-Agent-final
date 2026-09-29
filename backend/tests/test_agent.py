"""Test autonomous agent, hypothesis engine, and recommendation engine."""
import pytest
from app.agents.incident_agent import get_incident_agent
from app.agents.hypothesis_engine import HypothesisEngine
from app.agents.recommendation_engine import RecommendationEngine
from app.services.runbook_service import get_runbook_service


def test_hypothesis_generation():
    engine = HypothesisEngine()
    incident = {
        "title": "API Gateway High CPU",
        "service": "api-gateway",
        "symptoms": ["CPU continuously increasing", "memory increasing", "recent deployment"],
        "metrics": {"cpu_percent": 94},
        "deployment": {"recent": True, "version": "v2.1.0"},
    }
    hypotheses = engine.generate_hypotheses(incident)
    assert len(hypotheses) > 0
    assert any("memory" in h.cause.lower() or "cpu" in h.cause.lower() for h in hypotheses)
    assert hypotheses[0].confidence > 0.5
    assert len(hypotheses[0].evidence) > 0


def test_runbook_matching():
    rb_service = get_runbook_service()
    matched = rb_service.match_runbooks(
        service="api-gateway",
        symptoms=["memory leak", "memory increasing"],
        hypotheses=["Deployment-related memory leak"],
    )
    assert len(matched) > 0
    assert any("memory leak" in rb["name"].lower() for rb in matched)


def test_recommendation_engine():
    rec_engine = RecommendationEngine()
    hyp_engine = HypothesisEngine()
    rb_service = get_runbook_service()

    incident = {
        "id": "IR-TEST",
        "service": "api-gateway",
        "symptoms": ["memory increasing", "recent deployment"],
        "metrics": {"cpu_percent": 92},
    }
    hypotheses = hyp_engine.generate_hypotheses(incident)
    matched_rbs = rb_service.match_runbooks(
        service="api-gateway",
        symptoms=incident["symptoms"],
        hypotheses=[h.cause for h in hypotheses],
    )
    rec_set = rec_engine.generate_recommendations(
        incident=incident,
        hypotheses=hypotheses,
        matched_runbooks=matched_rbs,
    )

    assert rec_set.primary_recommendation is not None
    assert "rollback" in rec_set.primary_recommendation.action.lower() or "restart" in rec_set.primary_recommendation.action.lower()
    assert rec_set.confidence > 0.0


def test_agent_analyze_endpoint(client):
    create_res = client.post("/api/incidents/simulate", json={"incident_type": "high_cpu"})
    inc_id = create_res.json()["id"]

    analyze_res = client.post(f"/api/agents/analyze/{inc_id}")
    assert analyze_res.status_code == 200
    data = analyze_res.json()
    assert data["incident_id"] == inc_id
    assert len(data["hypotheses"]) > 0
    assert len(data["recommended_actions"]) > 0
    assert data["requires_human_approval"] is True
