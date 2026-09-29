"""Test incidents router endpoints."""


def test_create_and_get_incident(client):
    payload = {
        "title": "API Gateway Latency Spike",
        "service": "api-gateway",
        "severity": "HIGH",
        "description": "Latencies spiked past SLA limits",
        "symptoms": ["elevated p99", "timeouts"],
        "metrics": {"latency_ms": 2500},
        "logs": ["ERROR client timeout"],
        "deployment": {"recent": True, "version": "v1.2.0"},
    }
    res = client.post("/api/incidents", json=payload)
    assert res.status_code == 201
    created = res.json()
    assert created["id"].startswith("IR-")
    assert created["title"] == payload["title"]
    assert created["status"] == "OPEN"

    # Get by ID
    get_res = client.get(f"/api/incidents/{created['id']}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == created["id"]


def test_update_incident(client):
    create_res = client.post(
        "/api/incidents",
        json={
            "title": "Worker Crash",
            "service": "order-service",
            "severity": "CRITICAL",
            "description": "Worker crashed unexpectedly",
        },
    )
    inc_id = create_res.json()["id"]

    patch_res = client.patch(
        f"/api/incidents/{inc_id}",
        json={"status": "INVESTIGATING", "resolution_summary": "Investigating logs"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "INVESTIGATING"
    assert patch_res.json()["resolution_summary"] == "Investigating logs"


def test_simulate_incident(client):
    res = client.post("/api/incidents/simulate", json={"incident_type": "high_cpu"})
    assert res.status_code == 201
    data = res.json()
    assert "High CPU" in data["title"]
    assert data["service"] == "api-gateway"
    assert "cpu_percent" in data["metrics"]


def test_approve_and_reject_incident(client):
    create_res = client.post("/api/incidents/simulate", json={"incident_type": "memory_leak"})
    inc_id = create_res.json()["id"]

    # Reject
    rej_res = client.post(
        f"/api/incidents/{inc_id}/reject",
        json={"decision": "reject", "operator_comment": "Needs secondary verification"},
    )
    assert rej_res.status_code == 200
    assert rej_res.json()["status"] == "rejected"

    # Approve
    app_res = client.post(
        f"/api/incidents/{inc_id}/approve",
        json={"decision": "approve", "operator_comment": "Approved rollback"},
    )
    assert app_res.status_code == 200
    assert app_res.json()["status"] == "approved"
    assert app_res.json()["incident_status"] == "MITIGATED"


def test_invalid_input(client):
    res = client.post("/api/incidents", json={"invalid": "payload"})
    assert res.status_code == 422
