REASONS = {
    "FailedScheduling",
    "BackOff",
    "FailedMount",
    "FailedPull",
    "ErrImagePull",
    "Unhealthy",
    "Failed",
    "Killing",
}


def analyze_events(items: list[dict] | None = None) -> dict:
    """Summarize warning / failure Kubernetes events."""
    items = items or []
    findings = []
    for item in items:
        reason = item.get("reason") or ""
        event_type = item.get("type") or ""
        message = (item.get("message") or "")
        is_probe = any(hint in message.lower() for hint in (
            "liveness probe failed",
            "readiness probe failed",
            "startup probe failed",
        ))
        if event_type != "Warning" and reason not in REASONS and not is_probe:
            continue
        obj = item.get("involvedObject") or {}
        findings.append(
            {
                "reason": reason or event_type,
                "type": event_type,
                "message": message[:400],
                "namespace": (item.get("metadata") or {}).get("namespace") or obj.get("namespace"),
                "object": f"{obj.get('kind', 'Object')}/{obj.get('name', 'unknown')}",
                "count": item.get("count") or 1,
            }
        )
    known = [item for item in findings if item["reason"] in REASONS]
    selected = (known or findings)[:25]
    return {
        "warning_count": len(findings),
        "findings": selected,
        "detected": sorted({item["reason"] for item in selected}),
    }
