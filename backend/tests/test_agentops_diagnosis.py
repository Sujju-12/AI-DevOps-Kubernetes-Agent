import json

from app.ai.agentops import diagnose_with_metadata
from app.ai.llm import LlmNotConfiguredError
from app.models.schemas import Diagnosis


def test_diagnosis_metadata_reports_llm(monkeypatch) -> None:
    payload = {
        "root_cause": "test root cause",
        "explanation": "test explanation",
        "fix": "test fix",
        "kubectl_command": "kubectl get pods",
        "confidence": 80,
    }
    monkeypatch.setattr("app.ai.agentops.analyzer.complete", lambda _messages: json.dumps(payload))
    diagnosis, source = diagnose_with_metadata({"pods": {}, "logs": {}, "events": {}})
    assert isinstance(diagnosis, Diagnosis)
    assert source == "llm"


def test_diagnosis_metadata_reports_local_fallback(monkeypatch) -> None:
    def no_key(_messages):
        raise LlmNotConfiguredError("missing key")

    monkeypatch.setattr("app.ai.agentops.analyzer.complete", no_key)
    diagnosis, source = diagnose_with_metadata(
        {
            "pods": {"problematic_pods": [{"name": "api", "namespace": "demo", "status": "ImagePullBackOff"}]},
            "logs": {"pod_logs": []},
            "events": {"detected": ["ErrImagePull"]},
            "network": {"issues": []},
            "probes": {"failing_probes": []},
            "deployments": {"unhealthy_deployments": []},
        }
    )
    assert "image" in diagnosis.root_cause.lower()
    assert source == "local_fallback"
