"""Deterministic Senior SRE reasoning that runs fully offline."""

from app.models.schemas import Diagnosis


def diagnose(investigation: dict) -> Diagnosis:
    pods = investigation.get("pods") or {}
    logs = investigation.get("logs") or {}
    events = investigation.get("events") or {}
    deployments = investigation.get("deployments") or {}
    network = investigation.get("network") or {}

    problematic = pods.get("problematic_pods") or []
    pod_statuses = {p.get("status") for p in problematic}
    excerpts = "\n".join((entry.get("excerpt") or "") for entry in logs.get("pod_logs") or [])
    event_reasons = set(events.get("detected") or [])
    first_pod = problematic[0] if problematic else {}
    ns = first_pod.get("namespace") or "default"
    name = first_pod.get("name") or "workload"

    if {"ImagePullBackOff", "ErrImagePull"} & pod_statuses or "FailedPull" in event_reasons or "ErrImagePull" in event_reasons:
        return Diagnosis(
            root_cause="Invalid or unreachable container image tag",
            explanation=(
                "The pod cannot pull its image. Events show FailedPull/ErrImagePull "
                "and the pod is in ImagePullBackOff. The tag is likely wrong, private, or missing."
            ),
            fix="Update the deployment image to a valid local or reachable tag and recreate the pod.",
            kubectl_command=f"kubectl set image deployment/{_deployment_name(deployments, name)} {name}=<valid-image> -n {ns}",
            prevention="Pin images to digest and verify tags exist before applying manifests.",
            confidence=_confidence(True, True, "ImagePullBackOff" in pod_statuses),
            engine="heuristic",
        )

    if "OOMKilled" in pod_statuses or "oom" in excerpts.lower():
        return Diagnosis(
            root_cause="Container exceeded its memory limit (OOMKilled)",
            explanation=(
                "The container was killed by the kubelet because it used more memory than its limit. "
                "Restart loops will continue until the limit is raised or the app uses less memory."
            ),
            fix="Increase memory requests/limits on the deployment, then roll it out.",
            kubectl_command=(
                f"kubectl patch deployment {_deployment_name(deployments, name)} -n {ns} "
                "--type=json -p='[{\"op\":\"replace\",\"path\":\"/spec/template/spec/containers/0/resources/limits/memory\",\"value\":\"256Mi\"}]'"
            ),
            prevention="Set realistic memory requests/limits and add a memory metric alert.",
            confidence=_confidence(True, "OOMKilled" in pod_statuses, True),
            engine="heuristic",
        )

    if "CrashLoopBackOff" in pod_statuses or "BackOff" in event_reasons:
        missing_env = any(token in excerpts.lower() for token in ("database_url", "missing", "required", "not set", "environment"))
        return Diagnosis(
            root_cause="Application crash on startup"
            + (" because a required environment variable is missing" if missing_env else ""),
            explanation=(
                "The pod is in CrashLoopBackOff. Logs and restart counts indicate the process exits immediately. "
                + ("The logs mention a missing configuration/environment value." if missing_env else "Inspect the log excerpt for the exact exception.")
            ),
            fix=(
                "Add the missing secret/config value (for example DATABASE_URL) to the deployment and restart."
                if missing_env
                else "Fix the startup error shown in the logs, then rollout restart the deployment."
            ),
            kubectl_command=f"kubectl edit deployment {_deployment_name(deployments, name)} -n {ns}",
            prevention="Fail fast in the app if required env vars are missing, and add a startup probe.",
            confidence=_confidence(True, missing_env or bool(excerpts), True),
            engine="heuristic",
        )

    if "Pending" in pod_statuses or "FailedScheduling" in event_reasons:
        return Diagnosis(
            root_cause="Pod cannot be scheduled onto a node",
            explanation=(
                "The pod is Pending. FailedScheduling events usually mean insufficient CPU/memory, "
                "taints, or missing PersistentVolume claims."
            ),
            fix="Free node capacity, relax requests, or add a node that matches the pod's constraints.",
            kubectl_command=f"kubectl describe pod {name} -n {ns}",
            prevention="Keep resource requests realistic and monitor node allocatable capacity.",
            confidence=_confidence(True, "FailedScheduling" in event_reasons, True),
            engine="heuristic",
        )

    network_issues = network.get("issues") or []
    if network_issues:
        issue = network_issues[0]
        mismatch = issue.get("issue") == "selector_mismatch"
        return Diagnosis(
            root_cause="Service selector does not match pod labels"
            if mismatch
            else "Service has no ready endpoints",
            explanation=(
                f"Service {issue.get('service')} in {issue.get('namespace')} uses selector "
                f"{issue.get('selector')} but no matching ready pods/endpoints were found. "
                "Traffic cannot reach the workload."
            ),
            fix="Align the Service selector with the pod labels, or fix the pod so it becomes Ready.",
            kubectl_command=f"kubectl edit svc {issue.get('service')} -n {issue.get('namespace')}",
            prevention="Use the same label set in Deployment template labels and Service selector.",
            confidence=_confidence(True, True, True),
            engine="heuristic",
        )

    if not pods.get("healthy", True) or not deployments.get("healthy", True):
        return Diagnosis(
            root_cause="Unhealthy Kubernetes workload detected",
            explanation="The investigation found unhealthy pods or deployments. Review the collected evidence for the failing object.",
            fix="Inspect the listed pods and deployments, then apply the specific fix for their status.",
            kubectl_command="kubectl get pods,deploy,svc -A",
            prevention="Add readiness/liveness probes and alert on CrashLoopBackOff and Unschedulable pods.",
            confidence=70,
            engine="heuristic",
        )

    return Diagnosis(
        root_cause="No critical Kubernetes issues detected",
        explanation="Cluster appears healthy. Pods, deployments, and services returned no critical failure signals.",
        fix="No change required. Continue monitoring and re-run investigation if symptoms return.",
        kubectl_command="kubectl get pods -A",
        prevention="Keep regular investigations and readiness probes enabled.",
        confidence=80,
        engine="heuristic",
    )


def _deployment_name(deployments: dict, fallback: str) -> str:
    unhealthy = deployments.get("unhealthy_deployments") or []
    if unhealthy:
        return unhealthy[0].get("name") or fallback
    return fallback.rsplit("-", 1)[0] if fallback else "workload"


def _confidence(*signals: bool) -> int:
    score = 60 + 12 * sum(1 for signal in signals if signal)
    return min(96, score)
