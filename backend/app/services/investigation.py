"""Orchestrate kubectl evidence collection like a junior DevOps engineer."""

from pathlib import Path

from loguru import logger

from app.core.config import get_settings
from app.core.errors import friendly_kubectl_error
from app.core.messages import KUBECONFIG_MISSING
from app.kubernetes.deployments import inspect_deployments
from app.kubernetes.events import analyze_events
from app.kubernetes.executor import run_kubectl
from app.kubernetes.logs import collect_logs_for_pods
from app.kubernetes.network import inspect_network
from app.kubernetes.pods import inspect_pods
from app.kubernetes.probes import inspect_probes
from app.models.schemas import InvestigateResponse


class ClusterUnreachableError(RuntimeError):
    pass


def investigate(
    context: str | None = None,
    namespace: str | None = None,
    on_progress=None,
) -> InvestigateResponse:
    try:
        payload = collect_evidence(context=context, namespace=namespace, on_progress=on_progress)
        return InvestigateResponse(status="success", investigation=payload)
    except ClusterUnreachableError as exc:
        logger.warning("Investigation could not reach the cluster: {}", exc)
        return InvestigateResponse(
            status="error",
            investigation={
                "pods": {},
                "logs": {},
                "events": {},
                "deployments": {},
                "network": {},
                "probes": {},
            },
            message=str(exc),
        )


def collect_evidence(context: str | None = None, namespace: str | None = None, on_progress=None) -> dict:
    kubeconfig = Path(get_settings().kubeconfig_path).expanduser()
    if not kubeconfig.is_file():
        raise ClusterUnreachableError(KUBECONFIG_MISSING)

    ns_args = ["-n", namespace] if namespace else ["-A"]

    if on_progress:
        on_progress("pods")
    pods_raw = _json(["get", "pods", *ns_args, "-o", "json"], context)
    pods = inspect_pods(pods_raw.get("items") or [])

    def fetch_logs(ns: str, name: str) -> str:
        result = run_kubectl(
            ["logs", "-n", ns, name, "--tail=80", "--all-containers=true"],
            context=context,
        )
        return result.stdout if result.success else result.stderr

    if on_progress:
        on_progress("logs")
    events_raw = _json(["get", "events", *ns_args, "-o", "json"], context)
    if on_progress:
        on_progress("events")
    events = analyze_events(events_raw.get("items") or [])
    probes = inspect_probes(pods_raw.get("items") or [], events_raw.get("items") or [])

    log_targets = list(pods.get("problematic_pods") or [])
    seen = {(item.get("namespace"), item.get("name")) for item in log_targets}
    for item in probes.get("failing_probes") or []:
        key = (item.get("namespace"), item.get("pod"))
        if key in seen:
            continue
        seen.add(key)
        log_targets.append({"namespace": item.get("namespace"), "name": item.get("pod"), "status": "ProbeFailed"})
    logs = collect_logs_for_pods(fetch_logs, log_targets)

    if on_progress:
        on_progress("deployments")
    deployments = inspect_deployments(_json(["get", "deployments", *ns_args, "-o", "json"], context).get("items") or [])
    services = _json(["get", "svc", *ns_args, "-o", "json"], context)
    endpoints = _json(["get", "endpoints", *ns_args, "-o", "json"], context)
    if on_progress:
        on_progress("network")
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
        "probes": probes,
    }


def _json(args: list[str], context: str | None) -> dict:
    result = run_kubectl(args, context=context)
    parsed = result.parsed_json()
    if parsed is None:
        raise ClusterUnreachableError(_friendly(result.stderr or result.stdout))
    return parsed if isinstance(parsed, dict) else {"items": parsed}


def _friendly(stderr: str) -> str:
    return friendly_kubectl_error(stderr)
