from pathlib import Path

import yaml
from loguru import logger

from app.core.config import get_settings
from app.models.schemas import ClusterContext, ClusterListResponse


def _help(path: Path) -> str:
    return (
        f"Unable to read local kubeconfig at {path}. "
        "On Docker/WSL the file must exist on the Linux side (usually ~/.kube/config) "
        "and be mounted into the backend container. "
        "Set KUBECONFIG_HOST_PATH in a project .env to your real config, then recreate the backend. "
        "To try the UI without a cluster, restart with DEMO_MODE=true."
    )


def list_clusters() -> ClusterListResponse:
    settings = get_settings()
    path = Path(settings.kubeconfig_path).expanduser()
    if not path.exists():
        logger.warning("Kubeconfig not found at {}", path)
        return ClusterListResponse(
            kubeconfig_path=str(path),
            warning=_help(path),
        )

    try:
        data = yaml.safe_load(path.read_text()) or {}
    except (OSError, yaml.YAMLError) as exc:
        logger.error("Failed to parse kubeconfig: {}", exc)
        return ClusterListResponse(
            kubeconfig_path=str(path),
            warning=_help(path),
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

    contexts.sort(key=lambda item: (not item.is_current, item.name))
    return ClusterListResponse(
        kubeconfig_path=str(path),
        current_context=current,
        contexts=contexts,
        warning=None if contexts else "Kubeconfig has no contexts. Add a local cluster and retry.",
    )
