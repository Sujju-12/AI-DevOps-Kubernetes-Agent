from __future__ import annotations

import uuid
from datetime import datetime, timezone

from loguru import logger

from app.ai.agent import analyze_investigation
from app.core.config import get_settings
from app.kubernetes.clusters import demo_scenario_for_context, list_clusters
from app.kubernetes.deployments import inspect_deployments
from app.kubernetes.events import analyze_events
from app.kubernetes.executor import resolve_kubeconfig, run_kubectl
from app.kubernetes.logs import collect_logs_for_pods
from app.kubernetes.network import inspect_network
from app.kubernetes.pods import inspect_pods
from app.models.schemas import Diagnosis, InvestigateResponse, InvestigationRecord, ProgressStep
from app.services.fixtures import demo_investigation
from app.services.store import list_history, save_investigation

STEPS = [
    ("pods", "Checking Pods"),
    ("logs", "Reading Logs"),
    ("events", "Analyzing Events"),
    ("deployments", "Inspecting Deployments"),
    ("network", "Checking Networking"),
    ("ai", "AI Reasoning"),
    ("done", "Root Cause Found"),
]


class ClusterUnreachableError(RuntimeError):
    pass


async def investigate(context: str | None, namespace: str | None = None, demo_scenario: str | None = None) -> InvestigateResponse:
    settings = get_settings()
    job_id = str(uuid.uuid4())
    selected = context or list_clusters().current_context
    scenario = demo_scenario or demo_scenario_for_context(selected)
    use_demo = bool(settings.demo_mode or scenario or resolve_kubeconfig() is None)

    try:
        if use_demo:
            evidence = demo_investigation(scenario or "crashloop")
        else:
            try:
                evidence = _collect(selected, namespace)
            except ClusterUnreachableError as exc:
                if "kubeconfig file not found" in str(exc).lower() or "no such file" in str(exc).lower():
                    evidence = demo_investigation(scenario or "crashloop")
                else:
                    raise

        diagnosis = await analyze_investigation(evidence, selected)
        record = InvestigationRecord(
            id=job_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            context=selected,
            namespace=namespace,
            root_cause=diagnosis.root_cause,
            confidence=diagnosis.confidence,
            status="success",
        )
        save_investigation(record)
        return InvestigateResponse(
            status="success",
            job_id=job_id,
            cluster_context=selected,
            investigation=evidence,
            diagnosis=diagnosis,
            progress=[ProgressStep(key=k, label=l) for k, l in STEPS],
            history=list_history(),
        )
    except ClusterUnreachableError as exc:
        return _fail(job_id, selected, str(exc))
    except Exception as exc:  # noqa: BLE001
        logger.exception("Investigation failed")
        return _fail(job_id, selected, f"Investigation failed: {exc}")


def _collect(context: str | None, namespace: str | None) -> dict:
    ns_args = ["-n", namespace] if namespace else ["-A"]
    pods_raw = _json(["get", "pods", *ns_args, "-o", "json"], context)
    pods = inspect_pods(pods_raw.get("items") or [])

    def fetch_logs(ns: str, name: str) -> str:
        result = run_kubectl(["logs", "-n", ns, name, "--tail=80", "--all-containers=true"], context=context)
        return result.stdout if result.success else result.stderr

    logs = collect_logs_for_pods(fetch_logs, pods.get("problematic_pods") or [])
    events = analyze_events(_json(["get", "events", *ns_args, "-o", "json"], context).get("items") or [])
    deployments = inspect_deployments(_json(["get", "deployments", *ns_args, "-o", "json"], context).get("items") or [])
    svc = _json(["get", "svc", *ns_args, "-o", "json"], context)
    ep = _json(["get", "endpoints", *ns_args, "-o", "json"], context)
    network = inspect_network(svc.get("items") or [], ep.get("items") or [], pods_raw.get("items") or [])
    return {"pods": pods, "logs": logs, "events": events, "deployments": deployments, "network": network}


def _json(args: list[str], context: str | None) -> dict:
    result = run_kubectl(args, context=context)
    parsed = result.parsed_json()
    if parsed is None:
        raise ClusterUnreachableError(_friendly(result.stderr or result.stdout))
    return parsed if isinstance(parsed, dict) else {"items": parsed}


def _friendly(stderr: str) -> str:
    text = (stderr or "").strip()
    if "kubectl is not installed" in text:
        return "kubectl is not installed. Install kubectl, or use a demo cluster in the UI."
    return (
        "Unable to connect to Kubernetes cluster.\n\nPlease verify:\n"
        "- kubeconfig path\n- cluster access\n- kubectl permissions\n"
        f"\nDetails: {text or 'no output from kubectl'}"
    )


def _fail(job_id: str, context: str | None, message: str) -> InvestigateResponse:
    diagnosis = Diagnosis(
        root_cause="Investigation could not complete",
        explanation=message,
        fix="Fix cluster connectivity, then retry.",
        kubectl_command="kubectl cluster-info",
        confidence=0,
        engine="local",
    )
    record = InvestigationRecord(
        id=job_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        context=context,
        namespace=None,
        root_cause=diagnosis.root_cause,
        confidence=0,
        status="error",
    )
    save_investigation(record)
    return InvestigateResponse(
        status="error",
        job_id=job_id,
        cluster_context=context,
        diagnosis=diagnosis,
        error=message,
        progress=[ProgressStep(key=k, label=l, done=False) for k, l in STEPS],
        history=list_history(),
    )
