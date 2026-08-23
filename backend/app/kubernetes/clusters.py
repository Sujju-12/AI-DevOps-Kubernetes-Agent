import yaml
from loguru import logger

from app.core.config import get_settings
from app.kubernetes.executor import resolve_kubeconfig
from app.models.schemas import ClusterContext, ClusterListResponse

DEMO_CONTEXTS = (
    ("demo-crashloop", "CrashLoopBackOff — missing DATABASE_URL"),
    ("demo-imagepull", "ImagePullBackOff — invalid image tag"),
    ("demo-oom", "OOMKilled — memory limit too low"),
    ("demo-selector", "Service selector mismatch"),
    ("demo-healthy", "Healthy cluster"),
)


def demo_scenario_for_context(context: str | None) -> str | None:
    if not context or not context.startswith("demo-"):
        return None
    return context.removeprefix("demo-")


def _demo_list(warning: str, kubeconfig_path: str = "") -> ClusterListResponse:
    contexts = [
        ClusterContext(name=name, cluster="demo", server=label, is_current=index == 0)
        for index, (name, label) in enumerate(DEMO_CONTEXTS)
    ]
    return ClusterListResponse(
        kubeconfig_path=kubeconfig_path or get_settings().kubeconfig_path,
        current_context=contexts[0].name,
        contexts=contexts,
        warning=warning,
    )


def list_clusters() -> ClusterListResponse:
    path = resolve_kubeconfig()
    if path is None:
        tried = get_settings().kubeconfig_path
        logger.warning("No kubeconfig at {}", tried)
        return _demo_list(
            "No kubeconfig file found. Showing demo clusters so you can still try Investigate. "
            "Copy your config to ~/.kube/config (from WSL: /mnt/c/Users/<You>/.kube/config). "
            f"Looked at {tried}",
            tried,
        )

    try:
        data = yaml.safe_load(path.read_text()) or {}
    except (OSError, yaml.YAMLError) as exc:
        logger.error("Failed to parse kubeconfig: {}", exc)
        return _demo_list(f"Could not parse kubeconfig at {path}. Showing demo clusters.", str(path))

    clusters = {item.get("name"): item.get("cluster") or {} for item in data.get("clusters") or []}
    current = data.get("current-context")
    contexts: list[ClusterContext] = []
    for item in data.get("contexts") or []:
        ctx = item.get("context") or {}
        cluster_name = ctx.get("cluster") or ""
        info = clusters.get(cluster_name) or {}
        contexts.append(
            ClusterContext(
                name=item.get("name") or cluster_name,
                cluster=cluster_name,
                user=ctx.get("user") or "",
                namespace=ctx.get("namespace"),
                server=info.get("server"),
                is_current=item.get("name") == current,
            )
        )
    contexts.sort(key=lambda item: (not item.is_current, item.name))
    if not contexts:
        return _demo_list("Kubeconfig has no contexts. Showing demo clusters.", str(path))
    return ClusterListResponse(
        kubeconfig_path=str(path),
        current_context=current,
        contexts=contexts,
    )
