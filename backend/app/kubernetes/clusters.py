import yaml
from loguru import logger

from app.core.config import get_settings
from app.kubernetes.kubeconfig import kubeconfig_candidates, resolve_kubeconfig
from app.models.schemas import ClusterContext, ClusterListResponse

DEMO_CONTEXTS = (
    ("demo-crashloop", "crashloop", "CrashLoopBackOff — missing DATABASE_URL"),
    ("demo-imagepull", "imagepull", "ImagePullBackOff — invalid image tag"),
    ("demo-oom", "oom", "OOMKilled — memory limit too low"),
    ("demo-selector", "selector", "Service selector mismatch"),
    ("demo-healthy", "healthy", "Healthy cluster (no critical issues)"),
)


def demo_scenario_for_context(context: str | None) -> str | None:
    if not context:
        return None
    for name, scenario, _label in DEMO_CONTEXTS:
        if context == name:
            return scenario
    if context.startswith("demo-"):
        return context.removeprefix("demo-")
    return None


def demo_cluster_list(warning: str, kubeconfig_path: str = "") -> ClusterListResponse:
    contexts = [
        ClusterContext(
            name=name,
            cluster="demo",
            user="local",
            server=label,
            is_current=index == 0,
        )
        for index, (name, _scenario, label) in enumerate(DEMO_CONTEXTS)
    ]
    return ClusterListResponse(
        kubeconfig_path=kubeconfig_path,
        current_context=contexts[0].name,
        contexts=contexts,
        warning=warning,
    )


def list_clusters() -> ClusterListResponse:
    settings = get_settings()
    path = resolve_kubeconfig()
    if settings.demo_mode and path is None:
        return demo_cluster_list(
            "DEMO_MODE is on and no kubeconfig file was found. "
            "Select a demo cluster to investigate a built-in failure scenario."
        )
    if path is None:
        tried = ", ".join(str(item) for item in kubeconfig_candidates()[:4])
        logger.warning("Kubeconfig not found. Tried: {}", tried)
        return demo_cluster_list(
            "No kubeconfig file found, so local demo clusters are shown. "
            "Copy your config to ~/.kube/config (from Windows: "
            "/mnt/c/Users/<You>/.kube/config) and recreate the backend, "
            f"or set KUBECONFIG_HOST_DIR. Paths checked: {tried}"
        )

    try:
        data = yaml.safe_load(path.read_text()) or {}
    except (OSError, yaml.YAMLError) as exc:
        logger.error("Failed to parse kubeconfig {}: {}", path, exc)
        return demo_cluster_list(
            f"Kubeconfig at {path} could not be parsed. Showing demo clusters instead.",
            kubeconfig_path=str(path),
        )

    clusters = {item.get("name"): item.get("cluster") or {} for item in data.get("clusters") or []}
    current = data.get("current-context")
    contexts: list[ClusterContext] = []
    for item in data.get("contexts") or []:
        ctx = item.get("context") or {}
        cluster_name = ctx.get("cluster") or ""
        cluster_info = clusters.get(cluster_name) or {}
        contexts.append(
            ClusterContext(
                name=item.get("name") or cluster_name,
                cluster=cluster_name,
                user=ctx.get("user") or "",
                namespace=ctx.get("namespace"),
                server=cluster_info.get("server"),
                is_current=item.get("name") == current,
            )
        )

    if settings.demo_mode:
        demo = demo_cluster_list("Demo clusters are included because DEMO_MODE=true.")
        contexts = demo.contexts + contexts

    contexts.sort(key=lambda item: (not item.is_current, item.name))
    if not contexts:
        return demo_cluster_list(
            "Kubeconfig has no contexts. Showing demo clusters instead.",
            kubeconfig_path=str(path),
        )
    return ClusterListResponse(
        kubeconfig_path=str(path),
        current_context=current or contexts[0].name,
        contexts=contexts,
        warning=None,
    )
