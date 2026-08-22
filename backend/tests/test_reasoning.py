from app.ai.heuristics import diagnose
from app.kubernetes.deployments import inspect_deployments
from app.kubernetes.events import analyze_events
from app.kubernetes.network import inspect_network
from app.kubernetes.pods import inspect_pods
from app.services.fixtures import demo_investigation


def test_crashloop_root_cause() -> None:
    diagnosis = diagnose(demo_investigation("crashloop"))
    assert "environment" in diagnosis.root_cause.lower() or "crash" in diagnosis.root_cause.lower()
    assert diagnosis.confidence >= 80
    assert "kubectl" in diagnosis.kubectl_command


def test_imagepull_root_cause() -> None:
    diagnosis = diagnose(demo_investigation("imagepull"))
    assert "image" in diagnosis.root_cause.lower()


def test_oom_root_cause() -> None:
    diagnosis = diagnose(demo_investigation("oom"))
    assert "memory" in diagnosis.root_cause.lower() or "oom" in diagnosis.root_cause.lower()


def test_selector_mismatch_root_cause() -> None:
    diagnosis = diagnose(demo_investigation("selector"))
    assert "selector" in diagnosis.root_cause.lower()


def test_healthy_cluster() -> None:
    diagnosis = diagnose(demo_investigation("healthy"))
    assert "no critical" in diagnosis.root_cause.lower()


def test_pod_inspector_detects_crashloop() -> None:
    items = [
        {
            "metadata": {"name": "pay", "namespace": "default", "labels": {"app": "pay"}},
            "status": {
                "phase": "Running",
                "containerStatuses": [
                    {
                        "ready": False,
                        "restartCount": 6,
                        "state": {"waiting": {"reason": "CrashLoopBackOff"}},
                    }
                ],
            },
        }
    ]
    result = inspect_pods(items)
    assert result["healthy"] is False
    assert result["problematic_pods"][0]["status"] == "CrashLoopBackOff"


def test_events_and_network_and_deployments() -> None:
    events = analyze_events(
        [
            {
                "type": "Warning",
                "reason": "FailedPull",
                "message": "failed to pull",
                "metadata": {"namespace": "demo"},
                "involvedObject": {"kind": "Pod", "name": "x"},
            }
        ]
    )
    assert "FailedPull" in events["detected"]

    deployments = inspect_deployments(
        [
            {
                "metadata": {"name": "web", "namespace": "demo"},
                "spec": {"replicas": 2, "selector": {"matchLabels": {"app": "web"}}},
                "status": {
                    "availableReplicas": 0,
                    "unavailableReplicas": 2,
                    "conditions": [
                        {"type": "Available", "status": "False", "reason": "MinimumReplicasUnavailable"}
                    ],
                },
            }
        ]
    )
    assert deployments["healthy"] is False

    network = inspect_network(
        services=[
            {
                "metadata": {"name": "web", "namespace": "demo"},
                "spec": {"selector": {"app": "frontend"}},
            }
        ],
        endpoints=[],
        pods=[
            {
                "metadata": {
                    "name": "web-0",
                    "namespace": "demo",
                    "labels": {"app": "web"},
                }
            }
        ],
    )
    assert network["issues"][0]["issue"] == "selector_mismatch"
