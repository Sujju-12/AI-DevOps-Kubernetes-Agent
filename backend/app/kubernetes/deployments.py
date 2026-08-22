def inspect_deployments(items: list[dict]) -> dict:
    unhealthy = []
    for item in items:
        metadata = item.get("metadata") or {}
        spec = item.get("spec") or {}
        status = item.get("status") or {}
        desired = int(spec.get("replicas") or 0)
        available = int(status.get("availableReplicas") or 0)
        unavailable = int(status.get("unavailableReplicas") or 0)
        ready = int(status.get("readyReplicas") or 0)
        conditions = status.get("conditions") or []
        failing = [
            {
                "type": c.get("type"),
                "status": c.get("status"),
                "reason": c.get("reason"),
                "message": c.get("message"),
            }
            for c in conditions
            if c.get("type") in {"Available", "Progressing"}
            and (
                (c.get("type") == "Available" and c.get("status") != "True")
                or (c.get("reason") in {"ProgressDeadlineExceeded", "ReplicaFailure"})
            )
        ]
        if desired == available and not failing:
            continue
        if desired == 0 and available == 0:
            continue
        unhealthy.append(
            {
                "name": metadata.get("name"),
                "namespace": metadata.get("namespace"),
                "desired": desired,
                "ready": ready,
                "available": available,
                "unavailable": unavailable,
                "conditions": failing or conditions[:3],
                "selector": (spec.get("selector") or {}).get("matchLabels") or {},
            }
        )

    return {
        "healthy": len(unhealthy) == 0,
        "total_deployments": len(items),
        "unhealthy_deployments": unhealthy,
    }
