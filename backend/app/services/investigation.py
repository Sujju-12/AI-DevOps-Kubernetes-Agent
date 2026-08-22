from __future__ import annotations

import uuid
from datetime import datetime, timezone

from loguru import logger

from app.ai.agent import analyze_investigation, enrich_capture
from app.core.config import get_settings
from app.kubernetes.capture import ClusterUnreachableError, capture_cluster
from app.kubernetes.clusters import demo_scenario_for_context, list_clusters
from app.kubernetes.kubeconfig import resolve_kubeconfig
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
            capture = demo_investigation(scenario or "crashloop")
            for key, label in STEPS[:-2]:
                await progress_bus.publish(
                    job_id,
                    {"event": "progress", "step": key, "label": label, "done": True},
                )
        else:
            try:
                capture = await capture_cluster(job_id, selected_context, namespace)
            except ClusterUnreachableError as exc:
                if _should_fallback_to_demo(str(exc)):
                    logger.warning("No reachable cluster; using demo capture: {}", exc)
                    capture = demo_investigation(scenario or "crashloop")
                    for key, label in STEPS[:-2]:
                        await progress_bus.publish(
                            job_id,
                            {"event": "progress", "step": key, "label": label, "done": True},
                        )
                else:
                    raise ClusterUnreachableError(_friendly_kubectl(str(exc))) from exc

        evidence = enrich_capture(capture)

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
        await progress_bus.publish(job_id, {"event": "result", "payload": response.model_dump()})
        return response
    except ClusterUnreachableError as exc:
        return await _fail(job_id, selected_context, str(exc))
    except Exception as exc:  # noqa: BLE001
        logger.exception("Investigation failed")
        return await _fail(
            job_id,
            selected_context,
            f"Investigation failed: {exc}. Check kubeconfig, kubectl access, and backend logs.",
        )


def _should_fallback_to_demo(message: str) -> bool:
    text = message.lower()
    return (
        "no such file" in text
        or "kubeconfig file not found" in text
        or "stat /kube/config" in text
        or "skipped: no kubeconfig" in text
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
