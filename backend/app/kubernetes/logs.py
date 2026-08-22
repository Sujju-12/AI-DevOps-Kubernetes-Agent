"""Capture error lines from failing pods — keep excerpts short for the agent."""

LOG_SIGNALS = {
    "missing_env": ("database_url", "environment variable", "not set", "required env", "missing env"),
    "oom": ("oom", "out of memory", "cannot allocate"),
    "image": ("image", "pull", "manifest unknown", "not found"),
    "connection": ("connection refused", "dial tcp", "timeout", "no such host"),
    "exception": ("exception", "traceback", "panic", "fatal", "error"),
}


def summarize_logs(raw: str, max_lines: int = 30) -> dict:
    lines = [line.rstrip() for line in (raw or "").splitlines() if line.strip()]
    matched: list[str] = []
    signals: list[str] = []
    lower_blob = "\n".join(lines).lower()
    for name, needles in LOG_SIGNALS.items():
        if any(needle in lower_blob for needle in needles):
            signals.append(name)
    for line in lines:
        if any(needle in line.lower() for needles in LOG_SIGNALS.values() for needle in needles):
            matched.append(line)
    excerpt_lines = matched[-max_lines:] if matched else lines[-min(15, max_lines) :]
    return {
        "line_count": len(lines),
        "excerpt": "\n".join(excerpt_lines),
        "has_errors": bool(matched),
        "signals": signals,
    }


def collect_logs_for_pods(fetch_logs, problematic_pods: list[dict]) -> dict:
    collected = []
    for pod in problematic_pods[:8]:
        raw = fetch_logs(pod.get("namespace") or "default", pod.get("name") or "")
        collected.append(
            {
                "pod": pod.get("name"),
                "namespace": pod.get("namespace"),
                "status": pod.get("status"),
                **summarize_logs(raw),
            }
        )
    return {"pod_logs": collected, "pods_checked": len(collected)}
