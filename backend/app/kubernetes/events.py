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


def analyze_events(items: list[dict]) -> dict:
    findings = []
    for item in items:
        reason = item.get("reason") or ""
        event_type = item.get("type") or ""
        if event_type != "Warning" and reason not in REASONS:
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
    known = [f for f in findings if f["reason"] in REASONS]
    selected = (known or findings)[:25]
    return {"warning_count": len(findings), "findings": selected, "detected": sorted({f["reason"] for f in selected})}
