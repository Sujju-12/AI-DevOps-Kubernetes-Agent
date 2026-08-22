"""Summarize Kubernetes warning events the agent can correlate with pod state."""

KNOWN_FAILURES = {
    "FailedScheduling",
    "BackOff",
    "FailedMount",
    "FailedPull",
    "ErrImagePull",
    "Unhealthy",
    "Failed",
    "Killing",
    "FailedCreate",
    "FailedBinding",
    "NetworkNotReady",
}


def analyze_events(items: list[dict]) -> dict:
    findings = []
    for item in items:
        reason = item.get("reason") or ""
        event_type = item.get("type") or ""
        if event_type != "Warning" and reason not in KNOWN_FAILURES:
            continue
        obj = item.get("involvedObject") or {}
        findings.append(
            {
                "reason": reason or event_type,
                "type": event_type,
                "message": (item.get("message") or "")[:400],
                "namespace": (item.get("metadata") or {}).get("namespace") or obj.get("namespace"),
                "object": f"{obj.get('kind', 'Object')}/{obj.get('name', 'unknown')}",
                "count": item.get("count") or 1,
            }
        )
    known = [item for item in findings if item["reason"] in KNOWN_FAILURES]
    selected = (known or findings)[:25]
    return {
        "warning_count": len(findings),
        "findings": selected,
        "detected": sorted({item["reason"] for item in selected}),
    }
