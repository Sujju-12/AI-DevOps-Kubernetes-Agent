"""Local Senior SRE engine — correlates evidence when no LLM key is configured."""

from app.models.schemas import Diagnosis


def diagnose(investigation: dict) -> Diagnosis:
    pods = investigation.get("pods") or {}
    logs = investigation.get("logs") or {}
    events = investigation.get("events") or {}
    deployments = investigation.get("deployments") or {}
    network = investigation.get("network") or {}

    problematic = pods.get("problematic_pods") or []
    statuses = {p.get("status") for p in problematic}
    excerpts = "\n".join((e.get("excerpt") or "") for e in logs.get("pod_logs") or []).lower()
    reasons = set(events.get("detected") or [])
    first = problematic[0] if problematic else {}
    ns = first.get("namespace") or "default"
    name = first.get("name") or "workload"
    deploy = _deploy_name(deployments, name)

    if {"ImagePullBackOff", "ErrImagePull"} & statuses or {"FailedPull", "ErrImagePull"} & reasons:
        return Diagnosis(
            root_cause="Invalid or unreachable container image tag",
            explanation="The pod cannot pull its image. Events show FailedPull/ErrImagePull.",
            fix="Update the deployment image to a valid tag and recreate the pod.",
            kubectl_command=f"kubectl set image deployment/{deploy} {deploy}=<valid-image> -n {ns}",
            prevention="Pin images to a digest and verify tags before apply.",
            confidence=_score(True, True, "ImagePullBackOff" in statuses),
        )
    if "OOMKilled" in statuses or "oom" in excerpts:
        return Diagnosis(
            root_cause="Container exceeded its memory limit (OOMKilled)",
            explanation="The kubelet killed the container because it used more memory than its limit.",
            fix="Increase memory requests/limits on the deployment, then roll it out.",
            kubectl_command=f"kubectl edit deployment {deploy} -n {ns}",
            prevention="Set realistic memory limits and alert on OOMKilled.",
            confidence=_score(True, "OOMKilled" in statuses, True),
        )
    if "CrashLoopBackOff" in statuses or "BackOff" in reasons:
        missing_env = any(token in excerpts for token in ("database_url", "missing", "not set", "environment"))
        return Diagnosis(
            root_cause="Application crash on startup"
            + (" because a required environment variable is missing" if missing_env else ""),
            explanation="The pod is in CrashLoopBackOff. "
            + ("Logs mention a missing configuration value." if missing_env else "Inspect the log excerpt for the exception."),
            fix="Add the missing secret/config value and restart." if missing_env else "Fix the startup error shown in the logs.",
            kubectl_command=f"kubectl edit deployment {deploy} -n {ns}",
            prevention="Fail fast if required env vars are missing. Add a startup probe.",
            confidence=_score(True, missing_env or bool(excerpts), True),
        )
    if "Pending" in statuses or "FailedScheduling" in reasons:
        return Diagnosis(
            root_cause="Pod cannot be scheduled onto a node",
            explanation="The pod is Pending. FailedScheduling usually means CPU/memory, taints, or a missing volume.",
            fix="Free node capacity, lower requests, or add a matching node.",
            kubectl_command=f"kubectl describe pod {name} -n {ns}",
            prevention="Keep resource requests realistic.",
            confidence=_score(True, "FailedScheduling" in reasons, True),
        )
    issues = network.get("issues") or []
    if issues:
        issue = issues[0]
        mismatch = issue.get("issue") == "selector_mismatch"
        return Diagnosis(
            root_cause="Service selector does not match pod labels" if mismatch else "Service has no ready endpoints",
            explanation=f"Service {issue.get('service')} selector {issue.get('selector')} does not reach ready pods.",
            fix="Align the Service selector with pod labels, or make matching pods Ready.",
            kubectl_command=f"kubectl edit svc {issue.get('service')} -n {issue.get('namespace')}",
            prevention="Use the same labels on the Deployment template and Service selector.",
            confidence=_score(True, True, True),
        )
    if not pods.get("healthy", True) or not deployments.get("healthy", True):
        return Diagnosis(
            root_cause="Unhealthy Kubernetes workload detected",
            explanation="Unhealthy pods or deployments were found. Review the captured evidence.",
            fix="Inspect the listed objects and apply the fix for their status.",
            kubectl_command="kubectl get pods,deploy,svc -A",
            prevention="Alert on CrashLoopBackOff and ImagePullBackOff.",
            confidence=70,
        )
    return Diagnosis(
        root_cause="No critical Kubernetes issues detected",
        explanation="Cluster appears healthy. No critical pod, event, or service failures were captured.",
        fix="No change required.",
        kubectl_command="kubectl get pods -A",
        prevention="Keep readiness probes enabled.",
        confidence=82,
    )


def _deploy_name(deployments: dict, fallback: str) -> str:
    unhealthy = deployments.get("unhealthy_deployments") or []
    if unhealthy:
        return unhealthy[0].get("name") or fallback
    return fallback.rsplit("-", 1)[0] if fallback else "workload"


def _score(*signals: bool) -> int:
    return min(96, 60 + 12 * sum(1 for item in signals if item))
