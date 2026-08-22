"""Turn ranked Kubernetes issues into a concrete diagnosis and suggested fix."""

from app.ai.issues import Issue
from app.models.schemas import Diagnosis


def suggest(issues: list[Issue], capture: dict) -> Diagnosis:
    if not issues:
        return Diagnosis(
            root_cause="No critical Kubernetes issues detected",
            explanation="Captured pod, event, deployment, and service signals look healthy.",
            fix="No change required. Re-run the investigation if symptoms return.",
            kubectl_command="kubectl get pods,deploy,svc -A",
            prevention="Keep readiness probes and resource requests in every workload.",
            confidence=82,
            engine="agent",
            issue_type="healthy",
            evidence=["No unhealthy pods, warning events, or service selector problems were captured."],
        )

    primary = issues[0]
    extra = [item.summary for item in issues[1:3]]
    diagnosis = _for_issue(primary, capture)
    if extra:
        diagnosis.explanation = diagnosis.explanation + " Related findings: " + "; ".join(extra)
    diagnosis.issue_type = primary.issue_type
    diagnosis.evidence = primary.evidence or primary.signals
    diagnosis.engine = "agent"
    diagnosis.confidence = _confidence(primary, capture)
    return diagnosis


def _for_issue(issue: Issue, capture: dict) -> Diagnosis:
    deploy = _deployment_name(capture, issue.resource)
    ns = issue.namespace
    if issue.issue_type == "image_pull":
        return Diagnosis(
            root_cause="Invalid or unreachable container image tag",
            explanation=issue.summary + " FailedPull/ErrImagePull means the tag is wrong, private, or missing.",
            fix="Set the deployment image to a tag that exists locally or in the registry, then recreate the pod.",
            kubectl_command=f"kubectl set image deployment/{deploy} {deploy}=<valid-image> -n {ns}",
            prevention="Pin images by digest and verify tags before apply.",
        )
    if issue.issue_type == "oom_killed":
        return Diagnosis(
            root_cause="Container exceeded its memory limit (OOMKilled)",
            explanation=issue.summary + " The kubelet killed the process; it will restart until the limit is raised.",
            fix="Increase memory requests/limits on the deployment and roll it out.",
            kubectl_command=(
                f"kubectl patch deployment {deploy} -n {ns} --type=json "
                "-p='[{\"op\":\"replace\",\"path\":\"/spec/template/spec/containers/0/resources/limits/memory\",\"value\":\"256Mi\"}]'"
            ),
            prevention="Size memory from real usage and alert on OOMKilled.",
        )
    if issue.issue_type == "crash_loop":
        missing_env = any("missing_env" in signal for signal in issue.signals)
        return Diagnosis(
            root_cause=(
                "Application crash on startup because a required environment variable is missing"
                if missing_env
                else "Application crash on startup"
            ),
            explanation=issue.summary
            + (
                " Logs mention a missing configuration value such as DATABASE_URL."
                if missing_env
                else " Use the captured log excerpt to fix the startup exception."
            ),
            fix=(
                "Add the missing secret or config value to the deployment, then rollout restart."
                if missing_env
                else "Fix the startup error in the logs, then rollout restart the deployment."
            ),
            kubectl_command=f"kubectl edit deployment {deploy} -n {ns}",
            prevention="Fail fast when required env vars are missing and add a startup probe.",
        )
    if issue.issue_type == "pending":
        return Diagnosis(
            root_cause="Pod cannot be scheduled onto a node",
            explanation=issue.summary + " FailedScheduling usually means CPU/memory, taints, or a missing volume.",
            fix="Free node capacity, lower requests, or add a node that matches the pod constraints.",
            kubectl_command=f"kubectl describe pod {issue.resource} -n {ns}",
            prevention="Keep requests realistic and watch allocatable node capacity.",
        )
    if issue.issue_type == "selector_mismatch":
        return Diagnosis(
            root_cause="Service selector does not match pod labels",
            explanation=issue.summary + " Traffic cannot reach any pod.",
            fix="Align the Service selector with the Deployment pod template labels.",
            kubectl_command=f"kubectl edit svc {issue.resource} -n {ns}",
            prevention="Share one label set between the Deployment template and the Service selector.",
        )
    if issue.issue_type == "missing_endpoints":
        return Diagnosis(
            root_cause="Service has no ready endpoints",
            explanation=issue.summary + " Pods exist but are not Ready, or the selector is stale.",
            fix="Make matching pods Ready, or correct the Service selector.",
            kubectl_command=f"kubectl get endpoints {issue.resource} -n {ns} -o yaml",
            prevention="Use readiness probes so endpoints only include healthy pods.",
        )
    if issue.issue_type == "probe_unhealthy":
        return Diagnosis(
            root_cause="Readiness or liveness probe is failing",
            explanation=issue.summary,
            fix="Fix the probe path/port or the application listen address, then roll the deployment.",
            kubectl_command=f"kubectl describe pod {issue.resource} -n {ns}",
            prevention="Test probes locally and keep initialDelaySeconds realistic.",
        )
    return Diagnosis(
        root_cause="Unhealthy Kubernetes workload detected",
        explanation=issue.summary,
        fix="Inspect the captured resource and apply the fix for its status.",
        kubectl_command=f"kubectl get pods,deploy -n {ns}",
        prevention="Alert on CrashLoopBackOff, ImagePullBackOff, and Unschedulable pods.",
    )


def _deployment_name(capture: dict, fallback: str) -> str:
    unhealthy = (capture.get("deployments") or {}).get("unhealthy_deployments") or []
    if unhealthy:
        return unhealthy[0].get("name") or fallback
    name = fallback or "workload"
    return name.rsplit("-", 1)[0] if "-" in name else name


def _confidence(issue: Issue, capture: dict) -> int:
    score = 64
    if issue.evidence:
        score += 12
    if issue.signals:
        score += 10
    if (capture.get("events") or {}).get("detected"):
        score += 8
    return min(96, score)
