from app.kubernetes.deployments import inspect_deployments
from app.kubernetes.events import analyze_events
from app.kubernetes.logs import summarize_logs
from app.kubernetes.network import inspect_network
from app.kubernetes.pods import inspect_pods
from app.kubernetes.probes import inspect_probes


def test_inspect_pods_crashloop() -> None:
    result = inspect_pods(
        [
            {
                "metadata": {"name": "payment-service", "namespace": "default"},
                "status": {
                    "phase": "Running",
                    "containerStatuses": [
                        {
                            "ready": False,
                            "restartCount": 4,
                            "state": {"waiting": {"reason": "CrashLoopBackOff"}},
                        }
                    ],
                },
            }
        ]
    )
    assert result["healthy"] is False
    assert result["problematic_pods"][0]["status"] == "CrashLoopBackOff"


def test_summarize_logs_keeps_errors() -> None:
    summary = summarize_logs("ok\nFATAL: DATABASE_URL environment variable is missing\n")
    assert summary["has_errors"] is True
    assert "DATABASE_URL" in summary["excerpt"]


def test_analyze_events() -> None:
    result = analyze_events(
        [
            {
                "type": "Warning",
                "reason": "FailedPull",
                "message": "failed to pull image",
                "metadata": {"namespace": "demo"},
                "involvedObject": {"kind": "Pod", "name": "x"},
            }
        ]
    )
    assert "FailedPull" in result["detected"]


def test_inspect_deployments() -> None:
    result = inspect_deployments(
        [
            {
                "metadata": {"name": "web", "namespace": "demo"},
                "spec": {"replicas": 2, "selector": {"matchLabels": {"app": "web"}}},
                "status": {
                    "availableReplicas": 0,
                    "unavailableReplicas": 2,
                    "conditions": [{"type": "Available", "status": "False", "reason": "MinimumReplicasUnavailable"}],
                },
            }
        ]
    )
    assert result["healthy"] is False


def test_inspect_network_dns_events() -> None:
    result = inspect_network(
        services=[],
        endpoints=[],
        pods=[],
        events=[
            {
                "reason": "Failed",
                "message": "lookup payment.default.svc.cluster.local: NXDOMAIN",
                "involvedObject": {"kind": "Pod", "name": "web"},
            }
        ],
    )
    assert result["healthy"] is False
    assert result["dns_related"]


def test_inspect_probes_readiness_and_liveness() -> None:
    result = inspect_probes(
        pods=[
            {
                "metadata": {"name": "payment-service", "namespace": "default"},
                "spec": {
                    "containers": [
                        {
                            "name": "app",
                            "livenessProbe": {"httpGet": {"path": "/healthz", "port": 8080}},
                            "readinessProbe": {"httpGet": {"path": "/ready", "port": 8080}},
                        }
                    ]
                },
                "status": {
                    "phase": "Running",
                    "conditions": [{"type": "Ready", "status": "False"}],
                    "containerStatuses": [{"name": "app", "ready": False, "restartCount": 3}],
                },
            }
        ],
        events=[
            {
                "reason": "Unhealthy",
                "message": "Liveness probe failed: HTTP probe failed with statuscode: 500",
                "metadata": {"namespace": "default"},
                "involvedObject": {"kind": "Pod", "name": "payment-service"},
            },
            {
                "reason": "Unhealthy",
                "message": "Readiness probe failed: Get http://10.0.0.8:8080/ready: connection refused",
                "metadata": {"namespace": "default"},
                "involvedObject": {"kind": "Pod", "name": "payment-service"},
            },
        ],
    )
    assert result["healthy"] is False
    assert result["liveness_failures"] == 1
    assert result["readiness_failures"] == 1
    issue = result["failing_probes"][0]
    assert issue["liveness_probe"]["type"] == "httpGet"
    assert "/ready" in issue["readiness_probe"]["target"]


def test_inspect_network_selector_mismatch() -> None:
    result = inspect_network(
        services=[{"metadata": {"name": "web", "namespace": "demo"}, "spec": {"selector": {"app": "frontend"}}}],
        endpoints=[],
        pods=[{"metadata": {"name": "web-0", "namespace": "demo", "labels": {"app": "web"}}}],
    )
    assert result["issues"][0]["issue"] == "selector_mismatch"
