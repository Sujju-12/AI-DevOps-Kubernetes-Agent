from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app
from app.services.store import init_db


def setup_module() -> None:
    get_settings.cache_clear()
    init_db()


def test_health() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["service"] == "ai-kubernetes-agent"
    assert body["mode"] == "local"
