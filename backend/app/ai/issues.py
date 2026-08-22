from __future__ import annotations

from dataclasses import asdict, dataclass, field

from app.kubernetes.logs import LOG_SIGNALS


PRIORITY = {
    "image_pull": 100,
    "oom_killed": 90,
    "crash_loop": 80,
    "pending": 70,
    "probe_unhealthy": 60,
    "selector_mismatch": 50,
    "missing_endpoints": 45,
    "rollout_failed": 40,
}


@dataclass
class Issue:
    issue_type: str
    severity: str
    resource: str
    namespace: str
    summary: str
    signals: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def extract_issues(capture: dict) -> list[Issue]:
    """Turn captured kubectl evidence into a ranked list of Kubernetes issues."""
    issues: list[Issue] = []
    issues.extend(_from_pods(capture))
    issues.extend(_from_events(capture, issues))
    issues.extend(_from_network(capture))
    issues.extend(_from_deployments(capture, issues))
    issues.sort(key=lambda item: PRIORITY.get(item.issue_type, 0), reverse=True)
    return _dedupe(issues)


def _from_pods(capture: dict) -> list[Issue]:
    issues: list[Issue] = []
    log_index = {
        (entry.get("namespace"), entry.get("pod")): entry
        for entry in (capture.get("logs") or {}).get("pod_logs") or []
    }
    for pod in (capture.get("pods") or {}).get("problematic_pods") or []:
        status = pod.get("status") or ""
        key = (pod.get("namespace"), pod.get("name"))
        log = log_index.get(key) or {}
        log_signals = _signals_from_log(log)
        excerpt = (log.get("excerpt") or "").strip()
        evidence = [item for item in [pod.get("message"), excerpt] if item]
        if status in {"ImagePullBackOff", "ErrImagePull"}:
            issues.append(
                Issue(
                    "image_pull",
                    "critical",
                    pod.get("name") or "pod",
                    pod.get("namespace") or "default",
                    f"Pod {pod.get('name')} cannot pull its container image ({status}).",
                    signals=["pod:" + status, *log_signals],
                    evidence=evidence,
                )
            )
        elif status == "OOMKilled" or "oom" in log_signals:
            issues.append(
                Issue(
                    "oom_killed",
                    "critical",
                    pod.get("name") or "pod",
                    pod.get("namespace") or "default",
                    f"Container in {pod.get('name')} exceeded its memory limit.",
                    signals=["pod:" + status, *log_signals],
                    evidence=evidence,
                )
            )
        elif status in {"CrashLoopBackOff", "Error"} or "BackOff" in status:
            signals = ["pod:" + status, *log_signals]
            summary = f"Pod {pod.get('name')} is crash-looping."
            if "missing_env" in log_signals:
                summary = f"Pod {pod.get('name')} crash-loops because a required environment variable is missing."
            issues.append(
                Issue(
                    "crash_loop",
                    "critical",
                    pod.get("name") or "pod",
                    pod.get("namespace") or "default",
                    summary,
                    signals=signals,
                    evidence=evidence,
                )
            )
        elif status in {"Pending", "ContainerCreating"}:
            issues.append(
                Issue(
                    "pending",
                    "high",
                    pod.get("name") or "pod",
                    pod.get("namespace") or "default",
                    f"Pod {pod.get('name')} is stuck {status}.",
                    signals=["pod:" + status, *log_signals],
                    evidence=evidence,
                )
            )
    return issues


def _from_events(capture: dict, existing: list[Issue]) -> list[Issue]:
    issues: list[Issue] = []
    existing_types = {item.issue_type for item in existing}
    for finding in (capture.get("events") or {}).get("findings") or []:
        reason = finding.get("reason") or ""
        resource = (finding.get("object") or "object").split("/")[-1]
        namespace = finding.get("namespace") or "default"
        evidence = [finding.get("message") or reason]
        if reason in {"FailedPull", "ErrImagePull"} and "image_pull" not in existing_types:
            issues.append(
                Issue("image_pull", "critical", resource, namespace, "Image pull failed.", ["event:" + reason], evidence)
            )
        elif reason == "FailedScheduling" and "pending" not in existing_types:
            issues.append(
                Issue("pending", "high", resource, namespace, "Scheduler cannot place the pod.", ["event:" + reason], evidence)
            )
        elif reason == "Unhealthy" and "probe_unhealthy" not in existing_types:
            issues.append(
                Issue(
                    "probe_unhealthy",
                    "high",
                    resource,
                    namespace,
                    "Readiness or liveness probe is failing.",
                    ["event:" + reason],
                    evidence,
                )
            )
    return issues


def _from_network(capture: dict) -> list[Issue]:
    issues: list[Issue] = []
    for item in (capture.get("network") or {}).get("issues") or []:
        kind = item.get("issue") or "missing_endpoints"
        issue_type = "selector_mismatch" if kind == "selector_mismatch" else "missing_endpoints"
        issues.append(
            Issue(
                issue_type,
                "high",
                item.get("service") or "service",
                item.get("namespace") or "default",
                (
                    f"Service {item.get('service')} selector {item.get('selector')} matches no pods."
                    if issue_type == "selector_mismatch"
                    else f"Service {item.get('service')} has no ready endpoints."
                ),
                signals=["network:" + kind],
                evidence=[f"selector={item.get('selector')}"],
            )
        )
    return issues


def _from_deployments(capture: dict, existing: list[Issue]) -> list[Issue]:
    if existing:
        return []
    issues: list[Issue] = []
    for item in (capture.get("deployments") or {}).get("unhealthy_deployments") or []:
        issues.append(
            Issue(
                "rollout_failed",
                "medium",
                item.get("name") or "deployment",
                item.get("namespace") or "default",
                f"Deployment {item.get('name')} is not fully available "
                f"({item.get('ready')}/{item.get('desired')} ready).",
                signals=["deploy:unavailable"],
                evidence=[str(item.get("conditions") or "")],
            )
        )
    return issues


def _dedupe(issues: list[Issue]) -> list[Issue]:
    seen: set[tuple[str, str, str]] = set()
    unique: list[Issue] = []
    for issue in issues:
        key = (issue.issue_type, issue.namespace, issue.resource)
        if key in seen:
            continue
        seen.add(key)
        unique.append(issue)
    return unique


def _signals_from_log(log: dict) -> list[str]:
    if log.get("signals"):
        return list(log["signals"])
    excerpt = (log.get("excerpt") or "").lower()
    return [name for name, needles in LOG_SIGNALS.items() if any(needle in excerpt for needle in needles)]
