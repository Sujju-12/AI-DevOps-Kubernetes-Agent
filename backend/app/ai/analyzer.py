"""Root-cause analyzer: LLM reasoning first, local correlation if OpenRouter is unavailable."""

import json
import re

from loguru import logger

from app.ai.confidence import apply_confidence
from app.ai.fixes import apply_fix_defaults
from app.ai.llm import LlmError, LlmNotConfiguredError, complete
from app.ai.prompt import build_messages
from app.core.messages import CLUSTER_HEALTHY_ROOT_CAUSE
from app.models.schemas import Diagnosis


def diagnose(investigation: dict) -> Diagnosis:
    """Produce a Senior SRE diagnosis from Prompt 02 evidence."""
    try:
        raw = complete(build_messages(investigation))
        parsed = _parse_json(raw)
        diagnosis = _from_mapping(parsed)
    except LlmNotConfiguredError:
        logger.warning("OpenRouter key missing; using local evidence correlation")
        diagnosis = correlate_locally(investigation)
    except LlmError:
        logger.error("OpenRouter failed; using local evidence correlation")
        diagnosis = correlate_locally(investigation)
    except (ValueError, json.JSONDecodeError):
        logger.error("OpenRouter returned unparseable diagnosis; using local evidence correlation")
        diagnosis = correlate_locally(investigation)

    diagnosis = apply_confidence(investigation, diagnosis)
    return apply_fix_defaults(investigation, diagnosis)


def correlate_locally(investigation: dict) -> Diagnosis:
    """Correlate pods + logs + events without an LLM (graceful fallback)."""
    pods = (investigation.get("pods") or {}).get("problematic_pods") or []
    logs = investigation.get("logs") or {}
    events = (investigation.get("events") or {}).get("detected") or []
    network = (investigation.get("network") or {}).get("issues") or []
    probes = (investigation.get("probes") or {}).get("failing_probes") or []
    deployments = (investigation.get("deployments") or {}).get("unhealthy_deployments") or []
    excerpt = " ".join(item.get("excerpt") or "" for item in logs.get("pod_logs") or [])
    lowered = excerpt.lower()
    pod = pods[0] if pods else {}
    status = (pod.get("status") or "").lower()

    if "database_url" in lowered or ("missing" in lowered and "env" in lowered):
        name = pod.get("name") or "the workload"
        ns = pod.get("namespace") or "default"
        return Diagnosis(
            root_cause="Missing environment variable. The application cannot start without it.",
            explanation=(
                f"Pod {name} is in {pod.get('status') or 'CrashLoopBackOff'} and logs mention a missing "
                "configuration value (for example DATABASE_URL), which prevents startup."
            ),
            fix="Add the missing environment variable (or Secret) to the Deployment and roll it out.",
            kubectl_command=f"kubectl -n {ns} edit deployment {name}",
            prevention="Fail fast at startup if required env vars are unset, and keep them in Secrets.",
            confidence=90,
            confidence_reason="Pod crash state and logs both point at missing configuration.",
        )
    if "imagepullbackoff" in status or "errimagepull" in status or "FailedPull" in events or "ErrImagePull" in events:
        name = pod.get("name") or "the pod"
        ns = pod.get("namespace") or "default"
        return Diagnosis(
            root_cause="Invalid image tag. The container image cannot be pulled.",
            explanation=f"{name} is stuck pulling an image (ImagePullBackOff / ErrImagePull).",
            fix="Update the Deployment image to a valid name and tag (or add an imagePullSecret for a private registry).",
            kubectl_command=f"kubectl -n {ns} describe pod {name}",
            prevention="Pin image tags in CI and verify registry credentials before deploy.",
            confidence=88,
            confidence_reason="Pod status and pull events agree on an image pull failure.",
        )
    if "oomkilled" in status or "oomkilled" in lowered or "OOMKilled" in events:
        name = pod.get("name") or "the container"
        ns = pod.get("namespace") or "default"
        return Diagnosis(
            root_cause="Container exceeded memory limit (OOMKilled).",
            explanation=(
                f"{name} was killed because it used more memory than the pod limit. "
                "Kubernetes sets the last state to OOMKilled when this happens."
            ),
            fix="Increase memory requests/limits on the Deployment, or reduce the application's memory use.",
            kubectl_command=f"kubectl -n {ns} describe pod {name}",
            prevention="Set realistic memory limits and watch container_memory_working_set_bytes.",
            confidence=90,
            confidence_reason="Pod status or events report OOMKilled.",
        )
    if probes:
        item = probes[0]
        kind = "liveness" if item.get("liveness_failed") else "readiness"
        return Diagnosis(
            root_cause=f"The {kind} probe is failing, so Kubernetes keeps the pod unready or restarts it.",
            explanation="Probe-failed events and container Ready=False match a probe configuration or app health issue.",
            fix="Fix the probe path/port/delay, or make the application health endpoint succeed.",
            kubectl_command=f"kubectl -n {item.get('namespace') or 'default'} describe pod {item.get('pod')}",
            prevention="Align probe paths with the real health endpoints and give enough initialDelaySeconds.",
            confidence=84,
            confidence_reason="Probe config and Unhealthy probe events were both present.",
        )
    if network:
        item = network[0]
        issue = item.get("issue") or "networking"
        mismatch = issue == "selector_mismatch"
        return Diagnosis(
            root_cause=(
                "Service selector does not match pod labels."
                if mismatch
                else f"Service {item.get('service')} has a {issue.replace('_', ' ')}."
            ),
            explanation="Service selectors do not match ready pod endpoints, so traffic cannot reach the workload.",
            fix="Update the Service selector so it matches the Pod labels, then confirm Endpoints have IPs.",
            kubectl_command=(
                f"kubectl -n {item.get('namespace') or 'default'} get svc {item.get('service')} -o yaml"
            ),
            prevention="Use the same labels in Deployment spec.template and Service selector.",
            confidence=82,
            confidence_reason="Service selector and endpoint evidence agree.",
        )
    if pods:
        item = pods[0]
        ns = item.get("namespace") or "default"
        return Diagnosis(
            root_cause=f"Pod {item.get('name')} is unhealthy ({item.get('status')}).",
            explanation="The investigation found problematic pods; inspect describe/logs for the exact crash reason.",
            fix="Inspect the pod events and recent logs, then fix the application or resource limits.",
            kubectl_command=f"kubectl -n {ns} describe pod {item.get('name')} && kubectl -n {ns} logs {item.get('name')} --tail=80",
            prevention="Add resource requests/limits and working probes so failures surface earlier.",
            confidence=70,
            confidence_reason="Unhealthy pod status is present but logs did not name a single clear cause.",
        )
    if deployments:
        item = deployments[0]
        return Diagnosis(
            root_cause=f"Deployment {item.get('name')} is not fully available.",
            explanation="Desired replicas are not available, which usually follows a bad rollout or pod crash.",
            fix="Inspect the ReplicaSet and recent rollout events, then roll back if the new version is failing.",
            kubectl_command=f"kubectl -n {item.get('namespace') or 'default'} rollout status deployment/{item.get('name')}",
            prevention="Use rolling updates with a readiness probe and a progressDeadlineSeconds budget.",
            confidence=72,
            confidence_reason="Deployment replica counts show unavailability.",
        )
    return Diagnosis(
        root_cause=CLUSTER_HEALTHY_ROOT_CAUSE,
        explanation="Pods, deployments, probes, and services did not report a clear unhealthy signal.",
        fix="No Kubernetes change is required. If users still see errors, confirm the selected kubeconfig context.",
        kubectl_command="kubectl get pods -A && kubectl get events -A",
        prevention="Keep regular health checks and alerts on CrashLoopBackOff and FailedScheduling.",
        confidence=55,
        confidence_reason="Moderate confidence because the cluster evidence looks healthy.",
    )


def _from_mapping(data: dict) -> Diagnosis:
    confidence = data.get("confidence") or 0
    try:
        confidence = int(str(confidence).replace("%", "").strip() or 0)
    except ValueError:
        confidence = 0
    return Diagnosis(
        root_cause=str(data.get("root_cause") or "").strip() or "Unable to determine a root cause.",
        explanation=str(data.get("explanation") or "").strip(),
        fix=str(data.get("fix") or "").strip(),
        kubectl_command=str(data.get("kubectl_command") or data.get("kubectl_commands") or "").strip(),
        prevention=str(data.get("prevention") or "").strip(),
        confidence=confidence,
        confidence_reason=str(data.get("confidence_reason") or "").strip(),
    )


def _parse_json(raw: str) -> dict:
    text = (raw or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)
