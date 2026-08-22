from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app
from app.services.store import init_db


def _client(monkeypatch, tmp_path) -> TestClient:
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("DEMO_MODE", "true")
    get_settings.cache_clear()
    init_db()
    return TestClient(app)


def test_login_and_demo_investigate(monkeypatch, tmp_path) -> None:
    client = _client(monkeypatch, tmp_path)
    denied = client.post("/investigate", json={})
    assert denied.status_code == 401

    bad = client.post("/auth/login", json={"username": "admin", "password": "wrong"})
    assert bad.status_code == 401

    login = client.post("/auth/login", json={"username": "admin", "password": "admin"})
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    result = client.post("/investigate?demo_scenario=crashloop", json={}, headers=headers)
    assert result.status_code == 200
    body = result.json()
    assert body["status"] == "success"
    assert body["diagnosis"]["confidence"] > 0
    assert "DATABASE" in body["diagnosis"]["root_cause"].upper() or "environment" in body["diagnosis"]["root_cause"].lower() or "crash" in body["diagnosis"]["root_cause"].lower()

    history = client.get("/history", headers=headers)
    assert history.status_code == 200
    assert len(history.json()["items"]) >= 1


def test_investigate_demo_context_without_kubeconfig(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("DEMO_MODE", "false")
    monkeypatch.delenv("KUBECONFIG", raising=False)
    monkeypatch.setenv("KUBECONFIG_PATH", str(tmp_path / "missing"))
    monkeypatch.setenv("HOME", str(tmp_path / "empty-home"))
    get_settings.cache_clear()
    init_db()
    client = TestClient(app)
    login = client.post("/auth/login", json={"username": "admin", "password": "admin"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    clusters = client.get("/clusters", headers=headers)
    assert clusters.status_code == 200
    names = {item["name"] for item in clusters.json()["contexts"]}
    assert "demo-imagepull" in names

    result = client.post("/investigate", json={"context": "demo-imagepull"}, headers=headers)
    assert result.status_code == 200
    body = result.json()
    assert body["status"] == "success"
    assert "image" in body["diagnosis"]["root_cause"].lower()
