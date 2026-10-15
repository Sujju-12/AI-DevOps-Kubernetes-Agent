"""Low-cardinality, privacy-preserving AgentOps metrics.

Metrics contain outcome, diagnosis source, duration, and counts only. Never add
cluster names, namespace names, investigation IDs, log excerpts, prompts, or
secret values as metric attributes.
"""
from opentelemetry import metrics

_meter = metrics.get_meter("ai-kubernetes-agent.agentops")
_investigations = _meter.create_counter(
    "agentops.investigations",
    description="Number of completed Kubernetes investigation attempts",
    unit="{investigation}",
)
_duration = _meter.create_histogram(
    "agentops.investigation.duration",
    description="Wall-clock duration of a Kubernetes investigation request",
    unit="s",
)
_evidence_items = _meter.create_counter(
    "agentops.evidence_items",
    description="Evidence records collected by type",
    unit="{item}",
)


def evidence_counts(investigation: dict) -> dict[str, int]:
    """Count known evidence collections without retaining evidence contents."""
    groups = {
        "pods": ("pods", "problematic_pods"),
        "logs": ("logs", "pod_logs"),
        "events": ("events", "detected"),
        "deployments": ("deployments", "unhealthy_deployments"),
        "network": ("network", "issues"),
        "probes": ("probes", "failing_probes"),
    }
    counts = {}
    for label, (section, key) in groups.items():
        value = (investigation.get(section) or {}).get(key) or []
        counts[label] = len(value) if isinstance(value, list) else 0
    return counts


def record_investigation(
    *,
    outcome: str,
    diagnosis_source: str,
    duration_seconds: float,
    counts: dict[str, int] | None = None,
) -> None:
    """Record aggregate measurements; safe to call when telemetry is disabled."""
    attributes = {
        "outcome": outcome if outcome in {"success", "error"} else "error",
        "diagnosis_source": diagnosis_source
        if diagnosis_source in {"llm", "local_fallback", "not_run"}
        else "not_run",
    }
    _investigations.add(1, attributes)
    _duration.record(max(0.0, float(duration_seconds)), attributes)
    for kind, count in (counts or {}).items():
        if kind in {"pods", "logs", "events", "deployments", "network", "probes"} and count > 0:
            _evidence_items.add(count, {"evidence_type": kind})
