"""Test health endpoint."""

from fastapi.testclient import TestClient

from wedplan.main import app


def test_health_returns_ok() -> None:
    """Health endpoint returns status ok."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
