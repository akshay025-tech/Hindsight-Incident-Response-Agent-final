"""Integration test for the full Hindsight learning loop via REST API."""


def test_full_learning_loop_api(client):
    # Step 1: Demo Part 1 creates Incident A (IR-001)
    res_p1 = client.post("/api/simulation/demo-part1")
    assert res_p1.status_code == 200
    inc_a = res_p1.json()
    assert inc_a["id"] == "IR-001"

    # Step 2: Analyze Incident A
    res_analyze_a = client.post("/api/agents/analyze/IR-001")
    assert res_analyze_a.status_code == 200

    # Step 3: Approve remediation
    res_approve = client.post(
        "/api/incidents/IR-001/approve",
        json={"decision": "approve", "operator_comment": "Approved rollback"},
    )
    assert res_approve.status_code == 200

    # Step 4: Generate Postmortem for IR-001 & Retain in Hindsight
    res_pm = client.post(
        "/api/postmortems/IR-001",
        json={"operator_feedback": "Service stabilized after rollback."},
    )
    assert res_pm.status_code == 201
    assert res_pm.json()["retained_in_hindsight"] is True

    # Step 5: Demo Part 2 creates Incident B (IR-002)
    res_p2 = client.post("/api/simulation/demo-part2")
    assert res_p2.status_code == 200
    inc_b = res_p2.json()
    assert inc_b["id"] == "IR-002"

    # Step 6: Analyze Incident B (Hindsight Recall should trigger)
    res_analyze_b = client.post("/api/agents/analyze/IR-002")
    assert res_analyze_b.status_code == 200
    analysis_b = res_analyze_b.json()

    # Step 7: Verify learning loop assertions
    assert analysis_b["historical_memory_found"] is True
    assert len(analysis_b["historical_memories"]) > 0
    # Must reference IR-001 or memory leak
    all_recalled = " ".join(m["text"] for m in analysis_b["historical_memories"])
    assert "IR-001" in all_recalled or "memory leak" in all_recalled.lower()

    # Verify recommendations have historical support
    has_historical_support = any(
        rec.get("historical_support") == "IR-001" or "rollback" in rec.get("action", "").lower()
        for rec in analysis_b["recommended_actions"]
    )
    assert has_historical_support is True
