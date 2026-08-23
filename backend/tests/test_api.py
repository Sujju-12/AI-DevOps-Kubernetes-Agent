from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app
from app.services.store import init_db


def test_login_and_investigate(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "t.db"))
    monkeypatch.setenv("DEMO_MODE", "true")
    monkeypatch.delenv("KUBECONFIG", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path / "empty"))
    get_settings.cache_clear()
    init_db()
    client = TestClient(app)
    assert client.post("/investigate", json={}).status_code == 401
    login = client.post("/auth/login", json={"username": "admin", "password": "admin"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    result = client.post("/investigate?demo_scenario=crashloop", json={}, headers=headers)
    assert result.status_code == 200
    body = result.json()
    assert body["status"] == "success"
    assert body["diagnosis"]["confidence"] > 0
