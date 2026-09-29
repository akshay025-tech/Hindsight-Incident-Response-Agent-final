"""Test memory router endpoints."""


def test_memory_status(client):
    res = client.get("/api/memory/status")
    assert res.status_code == 200
    data = res.json()
    assert "bank_id" in data
    assert data["provider"] == "Hindsight"


def test_memory_recall(client):
    res = client.get("/api/memory/recall?query=memory+leak")
    assert res.status_code == 200
    data = res.json()
    assert "memories" in data


def test_memory_reflect(client):
    res = client.post("/api/memory/reflect", json={"query": "common causes of high CPU"})
    assert res.status_code == 200
    data = res.json()
    assert "available" in data


def test_memory_library(client):
    res = client.get("/api/memory/library")
    assert res.status_code == 200
    data = res.json()
    assert "memories" in data
    assert "count" in data
