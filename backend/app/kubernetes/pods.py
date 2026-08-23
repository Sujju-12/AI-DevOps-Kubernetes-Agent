UNHEALTHY = {
    "CrashLoopBackOff",
    "ImagePullBackOff",
    "ErrImagePull",
    "Pending",
    "Error",
    "OOMKilled",
    "ContainerCreating",
    "CreateContainerConfigError",
    "Failed",
}


def inspect_pods(items: list[dict]) -> dict:
    problematic = []
    for item in items:
        meta = item.get("metadata") or {}
        status = item.get("status") or {}
        phase = status.get("phase") or "Unknown"
        reason, ready, restarts = _pod_reason(status)
        unhealthy = phase in {"Pending", "Failed"} or reason in UNHEALTHY
        if phase == "Running" and ready and reason not in UNHEALTHY:
            unhealthy = False
        if not unhealthy:
            continue
        problematic.append(
            {
                "name": meta.get("name"),
                "namespace": meta.get("namespace"),
                "phase": phase,
                "status": reason or phase,
                "ready": ready,
                "restarts": restarts,
                "labels": meta.get("labels") or {},
            }
        )
    return {"healthy": not problematic, "total_pods": len(items), "problematic_pods": problematic}


def _pod_reason(status: dict) -> tuple[str, bool, int]:
    reason = status.get("reason") or status.get("phase") or "Unknown"
    ready = False
    restarts = 0
    waiting = None
    for container in status.get("containerStatuses") or []:
        restarts += int(container.get("restartCount") or 0)
        state = container.get("state") or {}
        last = container.get("lastState") or {}
        if "waiting" in state:
            waiting = (state["waiting"] or {}).get("reason")
        if "terminated" in state:
            waiting = (state["terminated"] or {}).get("reason") or waiting
        if "terminated" in last:
            waiting = waiting or (last["terminated"] or {}).get("reason")
        ready = ready or bool(container.get("ready"))
    conditions = {c.get("type"): c for c in status.get("conditions") or []}
    if "Ready" in conditions:
        ready = conditions["Ready"].get("status") == "True"
    if waiting == "OOMKilled":
        return "OOMKilled", ready, restarts
    return waiting or reason, ready, restarts
