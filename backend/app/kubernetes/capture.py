"""Collect kubectl evidence in a fixed order for the AI agent."""

from app.kubernetes.deployments import inspect_deployments
from app.kubernetes.events import analyze_events
from app.kubernetes.executor import run_kubectl
from app.kubernetes.logs import collect_logs_for_pods
from app.kubernetes.network import inspect_network
from app.kubernetes.pods import inspect_pods
from app.services.progress import progress_bus


class ClusterUnreachableError(RuntimeError):
    pass


async def capture_cluster(job_id: str, context: str | None, namespace: str | None) -> dict:
    ns_args = ["-n", namespace] if namespace else ["-A"]

    await progress_bus.publish(job_id, {"event": "progress", "step": "pods", "label": "Checking Pods", "done": False})
    pods_raw = _require_json(["get", "pods", *ns_args, "-o", "json"], context)
    pods = inspect_pods(pods_raw.get("items") or [])
    await progress_bus.publish(job_id, {"event": "progress", "step": "pods", "label": "Checking Pods", "done": True})

    await progress_bus.publish(job_id, {"event": "progress", "step": "logs", "label": "Reading Logs", "done": False})

    def fetch_logs(ns: str, name: str) -> str:
        result = run_kubectl(
            ["logs", "-n", ns, name, "--tail=80", "--all-containers=true"],
            context=context,
        )
        return result.stdout if result.success else result.stderr

    logs = collect_logs_for_pods(fetch_logs, pods.get("problematic_pods") or [])
    await progress_bus.publish(job_id, {"event": "progress", "step": "logs", "label": "Reading Logs", "done": True})

    await progress_bus.publish(
        job_id, {"event": "progress", "step": "events", "label": "Analyzing Events", "done": False}
    )
    events_raw = _require_json(["get", "events", *ns_args, "-o", "json"], context)
    events = analyze_events(events_raw.get("items") or [])
    await progress_bus.publish(
        job_id, {"event": "progress", "step": "events", "label": "Analyzing Events", "done": True}
    )

    await progress_bus.publish(
        job_id, {"event": "progress", "step": "deployments", "label": "Inspecting Deployments", "done": False}
    )
    deploy_raw = _require_json(["get", "deployments", *ns_args, "-o", "json"], context)
    deployments = inspect_deployments(deploy_raw.get("items") or [])
    await progress_bus.publish(
        job_id, {"event": "progress", "step": "deployments", "label": "Inspecting Deployments", "done": True}
    )

    await progress_bus.publish(
        job_id, {"event": "progress", "step": "network", "label": "Checking Networking", "done": False}
    )
    svc_raw = _require_json(["get", "svc", *ns_args, "-o", "json"], context)
    ep_raw = _require_json(["get", "endpoints", *ns_args, "-o", "json"], context)
    network = inspect_network(svc_raw.get("items") or [], ep_raw.get("items") or [], pods_raw.get("items") or [])
    await progress_bus.publish(
        job_id, {"event": "progress", "step": "network", "label": "Checking Networking", "done": True}
    )

    return {
        "pods": pods,
        "logs": logs,
        "events": events,
        "deployments": deployments,
        "network": network,
    }


def _require_json(args: list[str], context: str | None) -> dict:
    result = run_kubectl(args, context=context)
    parsed = result.parsed_json()
    if parsed is None:
        raise ClusterUnreachableError(result.stderr or result.stdout or "kubectl returned no JSON")
    if not isinstance(parsed, dict):
        return {"items": parsed}
    return parsed
