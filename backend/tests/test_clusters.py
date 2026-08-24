from app.ai.analyzer import correlate_locally
from app.core.messages import CLUSTER_HEALTHY_ROOT_CAUSE
from app.kubernetes.clusters import list_kube_contexts
from app.kubernetes.executor import KubectlResult


def test_correlate_oomkilled() -> None:
    diagnosis = correlate_locally(
        {
            "pods": {
                "problematic_pods": [
                    {"name": "memory-hog", "namespace": "demo", "status": "OOMKilled"}
                ]
            },
            "logs": {"pod_logs": []},
            "events": {"detected": ["OOMKilled"]},
        }
    )
    assert "memory" in diagnosis.root_cause.lower() or "oom" in diagnosis.root_cause.lower()
    assert "limit" in diagnosis.fix.lower()
    assert diagnosis.confidence >= 85


def test_correlate_healthy_cluster() -> None:
    diagnosis = correlate_locally(
        {
            "pods": {"problematic_pods": []},
            "logs": {"pod_logs": []},
            "events": {"detected": []},
            "network": {"issues": []},
            "probes": {"failing_probes": []},
            "deployments": {"unhealthy_deployments": []},
        }
    )
    assert diagnosis.root_cause == CLUSTER_HEALTHY_ROOT_CAUSE


def test_list_kube_contexts(monkeypatch) -> None:
    payload = """
    {
      "current-context": "kind-demo",
      "clusters": [{"name": "kind-demo", "cluster": {"server": "https://127.0.0.1:6443"}}],
      "contexts": [
        {"name": "kind-demo", "context": {"cluster": "kind-demo", "user": "kind-demo", "namespace": "default"}},
        {"name": "minikube", "context": {"cluster": "minikube", "user": "minikube"}}
      ]
    }
    """

    def fake_run(args, context=None, timeout=None):
        assert args[:2] == ["config", "view"]
        return KubectlResult(True, payload, "", "kubectl config view", 0)

    monkeypatch.setattr("app.kubernetes.clusters.run_kubectl", fake_run)
    monkeypatch.setattr('app.kubernetes.clusters.Path.is_file', lambda self: True)
    result = list_kube_contexts()
    assert result.status == "success"
    assert result.current_context == "kind-demo"
    names = [item.name for item in result.clusters]
    assert names == ["kind-demo", "minikube"]
    assert result.clusters[0].is_current is True
    assert result.clusters[0].server == "https://127.0.0.1:6443"
