# tests/test_health.py

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_ok():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["neo4j"] in ("up", "down")  # en pratique: "up"
