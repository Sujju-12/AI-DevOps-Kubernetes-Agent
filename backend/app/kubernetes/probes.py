"""Inspect readiness and liveness probes from pod specs and events."""


def inspect_probes(pods: list[dict] | None = None, events: list[dict] | None = None) -> dict:
    """Detect failing readiness, liveness, and startup probes."""
    pods = pods or []
    events = events or []
    issues = []
    event_index = _probe_events_by_pod(events)

    for pod in pods:
        meta = pod.get("metadata") or {}
        spec = pod.get("spec") or {}
        status = pod.get("status") or {}
        name = meta.get("name")
        namespace = meta.get("namespace")
        related = event_index.get(f"{namespace}/{name}", [])
        statuses = {item.get("name"): item for item in status.get("containerStatuses") or []}

        for container in spec.get("containers") or []:
            container_name = container.get("name")
            liveness = _summarize_probe(container.get("livenessProbe"))
            readiness = _summarize_probe(container.get("readinessProbe"))
            startup = _summarize_probe(container.get("startupProbe"))
            container_status = statuses.get(container_name) or {}
            container_ready = bool(container_status.get("ready"))
            restarts = int(container_status.get("restartCount") or 0)

            liveness_failed = any(item["probe"] == "liveness" for item in related)
            readiness_failed = any(item["probe"] == "readiness" for item in related)
            startup_failed = any(item["probe"] == "startup" for item in related)
            if readiness and status.get("phase") == "Running" and not container_ready:
                readiness_failed = True

            if not (liveness_failed or readiness_failed or startup_failed):
                continue

            issues.append(
                {
                    "pod": name,
                    "namespace": namespace,
                    "container": container_name,
                    "pod_ready": _is_ready(status),
                    "container_ready": container_ready,
                    "restarts": restarts,
                    "liveness_probe": liveness,
                    "readiness_probe": readiness,
                    "startup_probe": startup,
                    "liveness_failed": liveness_failed,
                    "readiness_failed": readiness_failed,
                    "startup_failed": startup_failed,
                    "events": related[:5],
                }
            )

    return {
        "healthy": not issues,
        "failing_probes": issues,
        "liveness_failures": sum(1 for item in issues if item["liveness_failed"]),
        "readiness_failures": sum(1 for item in issues if item["readiness_failed"]),
    }


def _is_ready(status: dict) -> bool:
    for condition in status.get("conditions") or []:
        if condition.get("type") == "Ready":
            return condition.get("status") == "True"
    return False


def _summarize_probe(probe: dict | None) -> dict | None:
    if not probe:
        return None
    kind = "unknown"
    target = ""
    if "httpGet" in probe:
        kind = "httpGet"
        http = probe["httpGet"] or {}
        target = f"{http.get('path') or '/'}:{http.get('port')}"
    elif "tcpSocket" in probe:
        kind = "tcpSocket"
        target = str((probe["tcpSocket"] or {}).get("port") or "")
    elif "exec" in probe:
        kind = "exec"
        target = " ".join(str(part) for part in ((probe["exec"] or {}).get("command") or [])[:6])
    elif "grpc" in probe:
        kind = "grpc"
        target = str((probe["grpc"] or {}).get("port") or "")
    return {
        "type": kind,
        "target": target.strip(),
        "initialDelaySeconds": probe.get("initialDelaySeconds"),
        "timeoutSeconds": probe.get("timeoutSeconds"),
        "periodSeconds": probe.get("periodSeconds"),
        "failureThreshold": probe.get("failureThreshold"),
    }


def _probe_events_by_pod(events: list[dict]) -> dict[str, list[dict]]:
    indexed: dict[str, list[dict]] = {}
    for item in events:
        message = item.get("message") or ""
        lowered = message.lower()
        probe = None
        if "liveness probe failed" in lowered:
            probe = "liveness"
        elif "readiness probe failed" in lowered:
            probe = "readiness"
        elif "startup probe failed" in lowered:
            probe = "startup"
        if probe is None:
            continue
        obj = item.get("involvedObject") or {}
        namespace = (item.get("metadata") or {}).get("namespace") or obj.get("namespace")
        name = obj.get("name")
        key = f"{namespace}/{name}"
        indexed.setdefault(key, []).append(
            {
                "probe": probe,
                "reason": item.get("reason") or "Unhealthy",
                "message": message[:300],
                "count": item.get("count") or 1,
            }
        )
    return indexed
