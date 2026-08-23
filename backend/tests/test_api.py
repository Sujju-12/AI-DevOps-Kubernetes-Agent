from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import Diagnosis


def test_investigate_endpoint_returns_structured_body(monkeypatch) -> None:
    fake = Diagnosis(
        root_cause="DATABASE_URL missing",
        explanation="Application cannot connect to DB.",
        fix="Add missing environment variable.",
        kubectl_command="kubectl edit deployment payment-service",
        confidence=92,
    )
    monkeypatch.setattr("app.api.routes.diagnose", lambda _investigation: fake)
    client = TestClient(app)
    response = client.post("/investigate", json={})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"success", "error"}
    assert "investigation" in body
    for key in ("pods", "logs", "events", "deployments", "network", "probes"):
        assert key in body["investigation"]
    if body["status"] == "success":
        assert body["diagnosis"]["root_cause"] == "DATABASE_URL missing"
        assert body["diagnosis"]["confidence"] == 92
