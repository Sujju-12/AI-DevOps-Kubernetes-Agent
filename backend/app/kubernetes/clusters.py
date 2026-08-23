"""List kubeconfig contexts so the UI can pick a cluster."""

from pathlib import Path

from app.core.config import get_settings
from app.core.messages import (
    CLUSTER_UNREACHABLE,
    KUBECONFIG_MISSING,
    KUBECTL_MISSING,
    KUBECTL_TIMEOUT,
    with_details,
)
from app.kubernetes.executor import run_kubectl
from app.models.schemas import ClusterContext, ClusterListResponse


def list_kube_contexts() -> ClusterListResponse:
    settings = get_settings()
    kubeconfig = Path(settings.kubeconfig_path).expanduser()
    kubeconfig_path = str(kubeconfig)

    if not kubeconfig.is_file():
        return ClusterListResponse(
            status="error",
            current_context=None,
            kubeconfig_path=kubeconfig_path,
            clusters=[],
            message=KUBECONFIG_MISSING,
        )

    result = run_kubectl(["config", "view", "-o", "json"])
    if not result.success:
        return ClusterListResponse(
            status="error",
            current_context=None,
            kubeconfig_path=kubeconfig_path,
            clusters=[],
            message=_friendly_kubectl(result.stderr or result.stdout),
        )

    data = result.parsed_json()
    if not isinstance(data, dict):
        return ClusterListResponse(
            status="error",
            current_context=None,
            kubeconfig_path=kubeconfig_path,
            clusters=[],
            message=with_details(CLUSTER_UNREACHABLE, result.stderr),
        )

    clusters_by_name = {
        item.get("name"): (item.get("cluster") or {})
        for item in (data.get("clusters") or [])
        if item.get("name")
    }
    current = data.get("current-context")
    contexts: list[ClusterContext] = []
    for item in data.get("contexts") or []:
        name = item.get("name")
        if not name:
            continue
        info = item.get("context") or {}
        cluster_name = info.get("cluster")
        cluster_spec = clusters_by_name.get(cluster_name) or {}
        contexts.append(
            ClusterContext(
                name=name,
                cluster=cluster_name,
                user=info.get("user"),
                namespace=info.get("namespace") or "default",
                server=cluster_spec.get("server"),
                is_current=name == current,
            )
        )

    if not contexts:
        return ClusterListResponse(
            status="error",
            current_context=current,
            kubeconfig_path=kubeconfig_path,
            clusters=[],
            message="No clusters were found in your kubeconfig file.",
        )

    return ClusterListResponse(
        status="success",
        current_context=current,
        kubeconfig_path=kubeconfig_path,
        clusters=contexts,
    )


def _friendly_kubectl(stderr: str) -> str:
    text = (stderr or "").strip()
    lowered = text.lower()
    if "kubectl is not installed" in lowered:
        return KUBECTL_MISSING
    if "timed out" in lowered:
        return KUBECTL_TIMEOUT
    if "no such file" in lowered or "stat" in lowered:
        return KUBECONFIG_MISSING
    return with_details(CLUSTER_UNREACHABLE, text)
