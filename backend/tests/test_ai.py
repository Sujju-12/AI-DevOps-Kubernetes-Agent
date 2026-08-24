from app.ai.analyzer import correlate_locally, diagnose
from app.ai.llm import LlmNotConfiguredError, complete
from app.ai.prompt import SYSTEM_PROMPT, build_prompt


def test_prompt_is_senior_sre_and_includes_sections() -> None:
    assert "Senior Kubernetes SRE" in SYSTEM_PROMPT
    text = build_prompt(
        {
            "pods": {"healthy": False},
            "logs": {"pod_logs": []},
            "events": {"findings": []},
            "deployments": {"healthy": True},
            "network": {"issues": []},
        }
    )
    assert "## Pod Status" in text
    assert "## Logs" in text
    assert "## Events" in text
    assert "## Deployment Health" in text
    assert "## Networking Findings" in text


def test_correlate_missing_database_url() -> None:
    diagnosis = correlate_locally(
        {
            "pods": {
                "problematic_pods": [
                    {"name": "payment-service", "namespace": "default", "status": "CrashLoopBackOff"}
                ]
            },
            "logs": {
                "pod_logs": [
                    {
                        "excerpt": "FATAL: DATABASE_URL environment variable is missing",
                        "has_errors": True,
                    }
                ]
            },
        }
    )
    assert "environment variable" in diagnosis.root_cause.lower()
    assert diagnosis.confidence >= 85
    assert "kubectl" in diagnosis.kubectl_command


def test_diagnose_prefers_openrouter_json(monkeypatch) -> None:
    def fake_complete(_messages):
        return (
            '{"root_cause":"DATABASE_URL missing","explanation":"App cannot connect to DB.",'
            '"fix":"Add the missing environment variable.","kubectl_command":"kubectl edit deployment payment-service",'
            '"prevention":"Validate env at startup.","confidence":92,"confidence_reason":"Logs and CrashLoop agree."}'
        )

    monkeypatch.setattr("app.ai.analyzer.complete", fake_complete)
    diagnosis = diagnose(
        {
            "pods": {"problematic_pods": [{"name": "payment-service", "status": "CrashLoopBackOff"}]},
            "logs": {"pod_logs": [{"excerpt": "DATABASE_URL missing", "has_errors": True}]},
            "events": {"findings": [{"reason": "BackOff"}]},
        }
    )
    assert diagnosis.root_cause == "DATABASE_URL missing"
    assert diagnosis.fix.startswith("Add the missing")
    assert diagnosis.confidence == 92


def test_complete_requires_env_key(monkeypatch) -> None:
    from app.core.config import Settings, get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    monkeypatch.setattr("app.ai.llm.get_settings", lambda: Settings(openrouter_api_key=""))
    try:
        complete([{"role": "user", "content": "hi"}])
        assert False, "expected LlmNotConfiguredError"
    except LlmNotConfiguredError:
        pass
    finally:
        get_settings.cache_clear()
