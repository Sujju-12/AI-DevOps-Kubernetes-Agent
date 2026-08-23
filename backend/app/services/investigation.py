"""Orchestrate kubectl evidence collection like a junior DevOps engineer."""

from loguru import logger

from app.kubernetes.deployments import inspect_deployments
from app.kubernetes.events import analyze_events
from app.kubernetes.executor import run_kubectl
from app.kubernetes.logs import collect_logs_for_pods
from app.kubernetes.network import inspect_network
from app.kubernetes.pods import inspect_pods
from app.models.schemas import InvestigateResponse


class ClusterUnreachableError(RuntimeError):
    pass


def investigate(context: str | None = None, namespace: str | None = None) -> InvestigateResponse:
    try:
        payload = collect_evidence(context=context, namespace=namespace)
        return InvestigateResponse(status="success", investigation=payload)
    except ClusterUnreachableError as exc:
        logger.warning("Investigation could not reach the cluster: {}", exc)
        return InvestigateResponse(
            status="error",
            investigation={"pods": {}, "logs": {}, "events": {}, "deployments": {}, "network": {}},
            message=str(exc),
        )


def collect_evidence(context: str | None = None, namespace: str | None = None) -> dict:
    ns_args = ["-n", namespace] if namespace else ["-A"]

    pods_raw = _json(["get", "pods", *ns_args, "-o", "json"], context)
    pods = inspect_pods(pods_raw.get("items") or [])

    def fetch_logs(ns: str, name: str) -> str:
        result = run_kubectl(
            ["logs", "-n", ns, name, "--tail=80", "--all-containers=true"],
            context=context,
        )
        return result.stdout if result.success else result.stderr

    logs = collect_logs_for_pods(fetch_logs, pods.get("problematic_pods") or [])
    events_raw = _json(["get", "events", *ns_args, "-o", "json"], context)
    events = analyze_events(events_raw.get("items") or [])
    deployments = inspect_deployments(_json(["get", "deployments", *ns_args, "-o", "json"], context).get("items") or [])
    services = _json(["get", "svc", *ns_args, "-o", "json"], context)
    endpoints = _json(["get", "endpoints", *ns_args, "-o", "json"], context)
    network = inspect_network(
        services.get("items") or [],
        endpoints.get("items") or [],
        pods_raw.get("items") or [],
        events_raw.get("items") or [],
    )
    return {
        "pods": pods,
        "logs": logs,
        "events": events,
        "deployments": deployments,
        "network": network,
    }


def _json(args: list[str], context: str | None) -> dict:
    result = run_kubectl(args, context=context)
    parsed = result.parsed_json()
    if parsed is None:
        raise ClusterUnreachableError(_friendly(result.stderr or result.stdout))
    return parsed if isinstance(parsed, dict) else {"items": parsed}


def _friendly(stderr: str) -> str:
    text = (stderr or "").strip()
    if "kubectl is not installed" in text:
        return "kubectl is not installed. Install kubectl and retry POST /investigate."
    return (
        "Unable to connect to Kubernetes cluster.\n\n"
        "Please verify:\n"
        "- kubeconfig path\n"
        "- cluster access\n"
        "- kubectl permissions\n"
        f"\nDetails: {text or 'no output from kubectl'}"
    )
