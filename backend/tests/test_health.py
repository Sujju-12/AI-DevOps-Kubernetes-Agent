from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import app


def test_health() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "ai-kubernetes-agent"}


def test_supabase_defaults() -> None:
    settings = Settings(openrouter_api_key="")
    assert settings.supabase_project_ref == "tzdxvhbdpkqckkmecytz"
    assert "tzdxvhbdpkqckkmecytz" in settings.supabase_url
