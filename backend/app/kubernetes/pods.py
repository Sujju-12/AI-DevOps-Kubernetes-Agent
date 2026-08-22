UNHEALTHY_REASONS = {
    "CrashLoopBackOff",
    "ImagePullBackOff",
    "ErrImagePull",
    "Pending",
    "Error",
    "OOMKilled",
    "ContainerCreating",
    "CreateContainerConfigError",
    "RunContainerError",
    "Failed",
}


def inspect_pods(items: list[dict]) -> dict:
    problematic = []
    for item in items:
        metadata = item.get("metadata") or {}
        status = item.get("status") or {}
        phase = status.get("phase") or "Unknown"
        reason, ready, restarts = _pod_reason(status)
        unhealthy = (
            phase not in {"Running", "Succeeded"}
            or reason in UNHEALTHY_REASONS
            or not ready
            or (phase == "Running" and restarts > 3 and reason in UNHEALTHY_REASONS)
        )
        if phase == "Running" and ready and reason not in UNHEALTHY_REASONS:
            unhealthy = False
        if reason in UNHEALTHY_REASONS or phase in {"Pending", "Failed"}:
            unhealthy = True
        if not unhealthy:
            continue
        problematic.append(
            {
                "name": metadata.get("name"),
                "namespace": metadata.get("namespace"),
                "phase": phase,
                "status": reason or phase,
                "ready": ready,
                "restarts": restarts,
                "labels": (metadata.get("labels") or {}),
            }
        )

    return {
        "healthy": len(problematic) == 0,
        "total_pods": len(items),
        "problematic_pods": problematic,
    }


def _pod_reason(status: dict) -> tuple[str, bool, int]:
    reason = status.get("reason") or status.get("phase") or "Unknown"
    ready = False
    restarts = 0
    waiting_reason = None
    for container in status.get("containerStatuses") or []:
        restarts += int(container.get("restartCount") or 0)
        state = container.get("state") or {}
        if "waiting" in state:
            waiting_reason = (state["waiting"] or {}).get("reason")
        if "terminated" in state:
            terminated = state["terminated"] or {}
            waiting_reason = terminated.get("reason") or waiting_reason
        ready = ready or bool(container.get("ready"))
    conditions = {c.get("type"): c for c in status.get("conditions") or []}
    ready_condition = conditions.get("Ready") or {}
    if ready_condition:
        ready = ready_condition.get("status") == "True"
    return waiting_reason or reason, ready, restarts
