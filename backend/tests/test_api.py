from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import Diagnosis, InvestigateResponse


def test_investigate_endpoint_returns_structured_body(monkeypatch) -> None:
    fake = Diagnosis(
        root_cause="DATABASE_URL missing",
        explanation="Application cannot connect to DB.",
        fix="Add missing environment variable.",
        kubectl_command="kubectl edit deployment payment-service",
        confidence=92,
    )
    monkeypatch.setattr("app.api.routes.investigate", lambda **_kwargs: _success_result())
    monkeypatch.setattr("app.api.routes.diagnose_with_metadata", lambda _investigation: (fake, "local_fallback"))
    monkeypatch.setattr("app.api.routes.patch_investigation", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("app.api.routes.mark_step", lambda _token, _id, steps, _key: steps)
    monkeypatch.setattr("app.api.routes.record_investigation", lambda **_kwargs: None)
    client = TestClient(app)
    response = client.post("/investigate", json={})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert "investigation" in body
    for key in ("pods", "logs", "events", "deployments", "network", "probes"):
        assert key in body["investigation"]
    assert body["diagnosis"]["root_cause"] == "DATABASE_URL missing"
    assert body["diagnosis"]["confidence"] == 92


def _success_result():
    return InvestigateResponse(
        status="success",
        investigation={
            "pods": {"problematic_pods": [{"name": "api", "status": "CrashLoopBackOff"}]},
            "logs": {"pod_logs": []},
            "events": {"detected": []},
            "deployments": {"unhealthy_deployments": []},
            "network": {"issues": []},
            "probes": {"failing_probes": []},
        },
        message="Investigation completed",
    )


def test_clusters_endpoint_returns_list(monkeypatch) -> None:
    from app.models.schemas import ClusterContext, ClusterListResponse

    fake = ClusterListResponse(
        status="success",
        current_context="kind-demo",
        kubeconfig_path="/tmp/kubeconfig",
        clusters=[
            ClusterContext(
                name="kind-demo",
                cluster="kind-demo",
                user="kind-demo",
                namespace="default",
                server="https://127.0.0.1:6443",
                is_current=True,
            )
        ],
    )
    monkeypatch.setattr("app.api.routes.list_kube_contexts", lambda: fake)
    client = TestClient(app)
    response = client.get("/clusters")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["clusters"][0]["name"] == "kind-demo"
    assert "certificate" not in str(body).lower()
