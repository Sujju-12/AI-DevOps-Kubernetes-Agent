from app.ai.analyzer import diagnose
from app.kubernetes.pods import inspect_pods
from app.services.fixtures import demo_investigation


def test_crashloop() -> None:
    d = diagnose(demo_investigation("crashloop"))
    assert "environment" in d.root_cause.lower() or "crash" in d.root_cause.lower()
    assert d.confidence >= 80


def test_imagepull() -> None:
    assert "image" in diagnose(demo_investigation("imagepull")).root_cause.lower()


def test_oom() -> None:
    text = diagnose(demo_investigation("oom")).root_cause.lower()
    assert "memory" in text or "oom" in text


def test_selector() -> None:
    assert "selector" in diagnose(demo_investigation("selector")).root_cause.lower()


def test_healthy() -> None:
    assert "no critical" in diagnose(demo_investigation("healthy")).root_cause.lower()


def test_pod_inspector() -> None:
    result = inspect_pods(
        [
            {
                "metadata": {"name": "pay", "namespace": "default"},
                "status": {
                    "phase": "Running",
                    "containerStatuses": [{"ready": False, "restartCount": 6, "state": {"waiting": {"reason": "CrashLoopBackOff"}}}],
                },
            }
        ]
    )
    assert result["problematic_pods"][0]["status"] == "CrashLoopBackOff"
