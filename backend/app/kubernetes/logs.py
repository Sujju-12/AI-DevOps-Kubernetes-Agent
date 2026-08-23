HINTS = (
    "exception",
    "error",
    "fatal",
    "traceback",
    "connection refused",
    "missing",
    "database_url",
    "oom",
    "image",
    "failed",
    "panic",
    "not set",
)


def summarize_logs(raw: str, max_lines: int = 40) -> dict:
    lines = [line.rstrip() for line in (raw or "").splitlines() if line.strip()]
    interesting = [line for line in lines if any(hint in line.lower() for hint in HINTS)]
    chosen = interesting[-max_lines:] if interesting else lines[-min(20, max_lines) :]
    return {"line_count": len(lines), "excerpt": "\n".join(chosen), "has_errors": bool(interesting)}


def collect_logs_for_pods(fetch_logs, problematic_pods: list[dict]) -> dict:
    collected = []
    for pod in problematic_pods[:8]:
        raw = fetch_logs(pod.get("namespace") or "default", pod.get("name") or "")
        collected.append({"pod": pod.get("name"), "namespace": pod.get("namespace"), "status": pod.get("status"), **summarize_logs(raw)})
    return {"pod_logs": collected, "pods_checked": len(collected)}
