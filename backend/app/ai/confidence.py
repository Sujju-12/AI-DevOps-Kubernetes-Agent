"""Turn evidence + model score into a 0-100 confidence value."""

from app.models.schemas import Diagnosis


def apply_confidence(investigation: dict, diagnosis: Diagnosis) -> Diagnosis:
    signals = _signals(investigation)
    base = diagnosis.confidence if diagnosis.confidence else 50
    if signals >= 3 and base < 80:
        base = min(95, base + 10)
    if signals == 0 and base > 70:
        base = 60
    diagnosis.confidence = max(5, min(99, int(base)))
    if not diagnosis.confidence_reason:
        diagnosis.confidence_reason = _reason(signals, investigation)
    return diagnosis


def _signals(investigation: dict) -> int:
    pods = investigation.get("pods") or {}
    logs = investigation.get("logs") or {}
    events = investigation.get("events") or {}
    deployments = investigation.get("deployments") or {}
    network = investigation.get("network") or {}
    probes = investigation.get("probes") or {}
    count = 0
    if pods.get("problematic_pods"):
        count += 1
    if logs.get("has_errors") or any(item.get("has_errors") for item in logs.get("pod_logs") or []):
        count += 1
    if events.get("findings"):
        count += 1
    if deployments.get("unhealthy_deployments"):
        count += 1
    if network.get("issues"):
        count += 1
    if probes.get("failing_probes"):
        count += 1
    return count


def _reason(signals: int, investigation: dict) -> str:
    pods = investigation.get("pods") or {}
    names = [item.get("status") for item in pods.get("problematic_pods") or [] if item.get("status")]
    if signals >= 3:
        extra = f" Pod states: {', '.join(names[:4])}." if names else ""
        return f"High confidence because multiple evidence sources agree.{extra}".strip()
    if signals == 0:
        return "Moderate confidence because no failing pods, events, or network issues were collected."
    return f"Confidence based on {signals} evidence source(s)."
