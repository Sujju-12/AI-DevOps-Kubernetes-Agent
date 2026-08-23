"""Map kubectl stderr to beginner-friendly messages."""

from pathlib import Path

from app.core.config import get_settings
from app.core.messages import (
    CLUSTER_UNREACHABLE,
    KUBECONFIG_MISSING,
    KUBECTL_MISSING,
    KUBECTL_TIMEOUT,
    with_details,
)


def friendly_kubectl_error(stderr: str | None = None) -> str:
    settings = get_settings()
    kubeconfig = Path(settings.kubeconfig_path).expanduser()
    text = (stderr or "").strip()
    lowered = text.lower()

    if not kubeconfig.is_file():
        return KUBECONFIG_MISSING
    if "kubectl is not installed" in lowered:
        return KUBECTL_MISSING
    if "timed out" in lowered:
        return KUBECTL_TIMEOUT
    if any(token in lowered for token in ("unauthorized", "forbidden", "you must be logged in")):
        return with_details(
            "Kubernetes rejected this request (authentication or permissions).\n\n"
            "Please verify:\n"
            "- kubeconfig user/credentials\n"
            "- RBAC permissions for get pods/events/services",
            text,
        )
    return with_details(CLUSTER_UNREACHABLE, text)
