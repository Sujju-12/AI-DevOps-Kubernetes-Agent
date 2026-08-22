from __future__ import annotations

import uuid
from datetime import datetime, timezone

from loguru import logger

from app.ai.analyzer import analyze_investigation
from app.core.config import get_settings
from app.kubernetes.clusters import demo_scenario_for_context, list_clusters
from app.kubernetes.kubeconfig import resolve_kubeconfig
from app.kubernetes.deployments import inspect_deployments
from app.kubernetes.events import analyze_events
from app.kubernetes.executor import run_kubectl
from app.kubernetes.logs import collect_logs_for_pods
from app.kubernetes.network import inspect_network
from app.kubernetes.pods import inspect_pods
from app.models.schemas import Diagnosis, InvestigateResponse, InvestigationRecord
from app.services.fixtures import demo_investigation
from app.services.progress import progress_bus
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


async def investigate(
    context: str | None,
    namespace: str | None = None,
    job_id: str | None = None,
    demo_scenario: str | None = None,
) -> InvestigateResponse:
    settings = get_settings()
    job_id = job_id or str(uuid.uuid4())
    selected_context = context or list_clusters().current_context
    scenario = demo_scenario or demo_scenario_for_context(selected_context)
    kubeconfig = resolve_kubeconfig()
    use_demo = bool(settings.demo_mode or scenario or kubeconfig is None)

    try:
        if use_demo:
            evidence = demo_investigation(scenario or "crashloop")
            for key, label in STEPS:
                await progress_bus.publish(
                    job_id,
                    {"event": "progress", "step": key, "label": label, "done": True},
                )
        else:
            try:
                evidence = await _collect_evidence(job_id, selected_context, namespace)
            except ClusterUnreachableError as exc:
                if _should_fallback_to_demo(str(exc)):
                    logger.warning("No reachable cluster; using demo investigation: {}", exc)
                    evidence = demo_investigation(scenario or "crashloop")
                    for key, label in STEPS:
                        await progress_bus.publish(
                            job_id,
                            {"event": "progress", "step": key, "label": label, "done": True},
                        )
                else:
                    raise

        await progress_bus.publish(
            job_id, {"event": "progress", "step": "ai", "label": "AI Reasoning", "done": False}
        )
        diagnosis = await analyze_investigation(evidence, selected_context)
        await progress_bus.publish(
            job_id, {"event": "progress", "step": "ai", "label": "AI Reasoning", "done": True}
        )
        await progress_bus.publish(
            job_id, {"event": "progress", "step": "done", "label": "Root Cause Found", "done": True}
        )

        record = InvestigationRecord(
            id=job_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            context=selected_context,
            namespace=namespace,
            root_cause=diagnosis.root_cause,
            confidence=diagnosis.confidence,
            status="success",
        )
        save_investigation(record)
        response = InvestigateResponse(
            status="success",
            job_id=job_id,
            cluster_context=selected_context,
            investigation=evidence,
            diagnosis=diagnosis,
            history=list_history(),
        )
        await progress_bus.publish(
            job_id, {"event": "result", "payload": response.model_dump()}
        )
        return response
    except ClusterUnreachableError as exc:
        return await _fail(job_id, selected_context, str(exc))
    except Exception as exc:  # noqa: BLE001
        logger.exception("Investigation failed")
        return await _fail(job_id, selected_context, _friendly_error(exc))


async def _collect_evidence(job_id: str, context: str | None, namespace: str | None) -> dict:
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
        raise ClusterUnreachableError(_friendly_kubectl(result.stderr or result.stdout))
    if not isinstance(parsed, dict):
        return {"items": parsed}
    return parsed


def _should_fallback_to_demo(message: str) -> bool:
    text = message.lower()
    return (
        "no such file" in text
        or "kubeconfig file not found" in text
        or "stat /kube/config" in text
    )


def _friendly_kubectl(stderr: str) -> str:
    text = (stderr or "").strip()
    if "kubectl is not installed" in text:
        return (
            "kubectl is not installed. Install kubectl locally, or set DEMO_MODE=true "
            "to run the built-in investigation fixtures."
        )
    return (
        "Unable to connect to Kubernetes cluster.\n\n"
        "Please verify:\n"
        "- kubeconfig path\n"
        "- cluster access\n"
        "- kubectl permissions\n"
        f"\nDetails: {text or 'no output from kubectl'}"
    )


def _friendly_error(exc: Exception) -> str:
    return f"Investigation failed: {exc}. Check kubeconfig, kubectl access, and backend logs."


async def _fail(job_id: str, context: str | None, message: str) -> InvestigateResponse:
    diagnosis = Diagnosis(
        root_cause="Investigation could not complete",
        explanation=message,
        fix="Fix cluster connectivity, then retry Investigate Cluster.",
        kubectl_command="kubectl cluster-info",
        prevention="Keep a valid local kubeconfig and kubectl on your PATH.",
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
    response = InvestigateResponse(
        status="error",
        job_id=job_id,
        cluster_context=context,
        diagnosis=diagnosis,
        error=message,
        history=list_history(),
    )
    await progress_bus.publish(job_id, {"event": "error", "message": message, "payload": response.model_dump()})
    return response
