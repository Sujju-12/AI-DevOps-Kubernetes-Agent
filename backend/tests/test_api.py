from fastapi.testclient import TestClient

from app.main import app


def test_investigate_endpoint_returns_structured_body() -> None:
    client = TestClient(app)
    response = client.post("/investigate", json={})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"success", "error"}
    assert "investigation" in body
    for key in ("pods", "logs", "events", "deployments", "network", "probes"):
        assert key in body["investigation"]
