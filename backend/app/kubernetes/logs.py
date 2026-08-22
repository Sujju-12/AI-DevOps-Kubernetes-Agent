ERROR_HINTS = (
    "exception",
    "error",
    "fatal",
    "traceback",
    "connection refused",
    "connection failure",
    "missing",
    "not found",
    "denied",
    "unauthorized",
    "database_url",
    "oom",
    "killed",
    "image",
    "failed",
    "panic",
)


def summarize_logs(raw: str, max_lines: int = 40) -> dict:
    lines = [line.rstrip() for line in raw.splitlines() if line.strip()]
    interesting = [
        line
        for line in lines
        if any(hint in line.lower() for hint in ERROR_HINTS)
    ]
    chosen = interesting[-max_lines:] if interesting else lines[-min(20, max_lines) :]
    return {
        "line_count": len(lines),
        "excerpt": "\n".join(chosen),
        "has_errors": bool(interesting),
    }


def collect_logs_for_pods(fetch_logs, problematic_pods: list[dict]) -> dict:
    collected = []
    for pod in problematic_pods[:8]:
        raw = fetch_logs(pod["namespace"], pod["name"])
        summary = summarize_logs(raw)
        collected.append(
            {
                "pod": pod["name"],
                "namespace": pod["namespace"],
                "status": pod.get("status"),
                **summary,
            }
        )
    return {"pod_logs": collected, "pods_checked": len(collected)}
