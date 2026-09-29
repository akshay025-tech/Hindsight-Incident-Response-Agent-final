"""Test postmortems endpoints and Hindsight retention."""


def test_postmortem_generation_and_retention(client):
    # Create and analyze incident
    create_res = client.post("/api/incidents/simulate", json={"incident_type": "high_cpu"})
    inc_id = create_res.json()["id"]
    client.post(f"/api/agents/analyze/{inc_id}")

    # Generate postmortem
    pm_res = client.post(
        f"/api/postmortems/{inc_id}",
        json={"operator_feedback": "Fast mitigation via recommended rollback."},
    )
    assert pm_res.status_code == 201
    pm = pm_res.json()
    assert pm["incident_id"] == inc_id
    assert len(pm["root_cause"]) > 0
    assert len(pm["timeline"]) > 0
    assert pm["retained_in_hindsight"] is True

    # Retrieve postmortem
    get_res = client.get(f"/api/postmortems/{inc_id}")
    assert get_res.status_code == 200
    assert get_res.json()["root_cause"] == pm["root_cause"]
