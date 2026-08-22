"""Extract Kubernetes failure signals from kubectl JSON."""

TERMINATED_PRIORITY = ("OOMKilled", "Error", "Completed")
WAITING_PRIORITY = (
    "ImagePullBackOff",
    "ErrImagePull",
    "CrashLoopBackOff",
    "CreateContainerConfigError",
    "InvalidImageName",
    "ContainerCreating",
)


def inspect_pods(items: list[dict]) -> dict:
    problematic = []
    for item in items:
        meta = item.get("metadata") or {}
        status = item.get("status") or {}
        phase = status.get("phase") or "Unknown"
        reason, ready, restarts, last_message = _summarize_status(status)
        if not _is_unhealthy(phase, reason, ready):
            continue
        problematic.append(
            {
                "name": meta.get("name"),
                "namespace": meta.get("namespace"),
                "phase": phase,
                "status": reason or phase,
                "ready": ready,
                "restarts": restarts,
                "message": last_message,
                "labels": meta.get("labels") or {},
            }
        )
    return {
        "healthy": not problematic,
        "total_pods": len(items),
        "problematic_pods": problematic,
    }


def _is_unhealthy(phase: str, reason: str, ready: bool) -> bool:
    if phase in {"Pending", "Failed"}:
        return True
    if reason in set(WAITING_PRIORITY + TERMINATED_PRIORITY):
        return True
    return phase == "Running" and not ready and reason not in {"Running", "Succeeded"}


def _summarize_status(status: dict) -> tuple[str, bool, int, str]:
    restarts = 0
    waiting = ""
    terminated = ""
    message = ""
    ready = False
    for container in status.get("containerStatuses") or []:
        restarts += int(container.get("restartCount") or 0)
        ready = ready or bool(container.get("ready"))
        state = container.get("state") or {}
        last = container.get("lastState") or {}
        if "waiting" in state:
            waiting = (state["waiting"] or {}).get("reason") or waiting
            message = (state["waiting"] or {}).get("message") or message
        if "terminated" in state:
            terminated = (state["terminated"] or {}).get("reason") or terminated
            message = (state["terminated"] or {}).get("message") or message
        if "terminated" in last:
            terminated = terminated or (last["terminated"] or {}).get("reason") or ""
            message = message or (last["terminated"] or {}).get("message") or ""
    conditions = {c.get("type"): c for c in status.get("conditions") or []}
    if "Ready" in conditions:
        ready = conditions["Ready"].get("status") == "True"
    reason = waiting or terminated or status.get("reason") or status.get("phase") or "Unknown"
    if terminated == "OOMKilled":
        reason = "OOMKilled"
    return reason, ready, restarts, message[:300]
