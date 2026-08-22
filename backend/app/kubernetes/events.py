EVENT_REASONS = {
    "FailedScheduling",
    "BackOff",
    "FailedMount",
    "FailedPull",
    "ErrImagePull",
    "Unhealthy",
    "Failed",
    "Killing",
    "FailedCreate",
    "InspectFailed",
}


def analyze_events(items: list[dict]) -> dict:
    findings = []
    for item in items:
        reason = ((item.get("reason") or "") if "reason" in item else "") or (
            (item.get("type") and item.get("reason")) or item.get("reason") or ""
        )
        # kubectl json: .reason, .type, .message, involvedObject
        event_reason = item.get("reason") or ""
        event_type = item.get("type") or ""
        if event_type != "Warning" and event_reason not in EVENT_REASONS:
            continue
        if event_reason not in EVENT_REASONS and event_type != "Warning":
            continue
        if event_reason not in EVENT_REASONS and event_type == "Warning":
            # keep warning events even if reason not in the known set
            pass
        elif event_reason not in EVENT_REASONS:
            continue
        obj = item.get("involvedObject") or {}
        findings.append(
            {
                "reason": event_reason or event_type,
                "type": event_type,
                "message": (item.get("message") or "")[:400],
                "namespace": item.get("metadata", {}).get("namespace") or obj.get("namespace"),
                "object": f"{obj.get('kind', 'Object')}/{obj.get('name', 'unknown')}",
                "count": item.get("count") or 1,
            }
        )

    # Prefer known failure reasons
    prioritized = [f for f in findings if f["reason"] in EVENT_REASONS]
    selected = (prioritized or findings)[:25]
    return {
        "warning_count": len(findings),
        "findings": selected,
        "detected": sorted({f["reason"] for f in selected}),
    }
