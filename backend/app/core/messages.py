"""Beginner-friendly error copy for the API and UI (no stack traces)."""

CLUSTER_UNREACHABLE = """Unable to connect to Kubernetes cluster.

Please verify:
- kubeconfig path
- cluster access
- kubectl permissions"""

KUBECONFIG_MISSING = """Unable to find a kubeconfig file.

Please verify:
- kubeconfig path (KUBECONFIG_PATH or ~/.kube/config)
- that the file exists and is readable
- cluster access
- kubectl permissions"""

KUBECTL_MISSING = """kubectl is not installed on the investigation server.

Install kubectl, then retry."""

KUBECTL_TIMEOUT = """The Kubernetes API request timed out.

Please verify:
- the cluster is reachable
- VPN or cloud credentials if the API is private
- kubectl permissions"""

UNEXPECTED = """Something went wrong while running the investigation.

Please retry. If this continues, check that the backend, kubeconfig, and OpenRouter key are configured."""

CLUSTER_HEALTHY_ROOT_CAUSE = "No critical Kubernetes issues detected. Cluster appears healthy."


def with_details(base: str, details: str | None = None) -> str:
    text = (details or "").strip()
    if not text:
        return base
    lowered = text.lower()
    if "traceback" in lowered or 'file "' in lowered:
        return base
    return f"{base}\n\nDetails: {text[:400]}"
