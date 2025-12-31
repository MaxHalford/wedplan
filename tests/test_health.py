"""Test health endpoint."""

from fastapi.testclient import TestClient

from wedplan.api.main import app


def test_health_returns_ok() -> None:
    """Health endpoint returns status ok and version."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
