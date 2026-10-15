from app.core.agentops_metrics import evidence_counts, record_investigation


def test_evidence_counts_only_counts_known_lists() -> None:
    evidence = {
        "pods": {"problematic_pods": [{"name": "a"}, {"name": "b"}]},
        "logs": {"pod_logs": [{"excerpt": "secret-like text"}]},
        "events": {"detected": []},
        "deployments": {"unhealthy_deployments": None},
        "network": {"issues": [{"issue": "selector_mismatch"}]},
        "probes": {"failing_probes": "unexpected"},
        "untrusted_extra": {"items": [{"secret": "never exported"}]},
    }
    assert evidence_counts(evidence) == {
        "pods": 2, "logs": 1, "events": 0, "deployments": 0, "network": 1, "probes": 0
    }


def test_record_investigation_accepts_only_known_low_cardinality_labels() -> None:
    # OpenTelemetry uses no-op instruments when export is disabled.
    record_investigation(
        outcome="something-unexpected",
        diagnosis_source="raw-cluster-name",
        duration_seconds=-1,
        counts={"pods": 2, "secret-label": 99},
    )
