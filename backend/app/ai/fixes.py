"""Fill in practical kubectl commands when the model omits them."""

from app.models.schemas import Diagnosis


def apply_fix_defaults(investigation: dict, diagnosis: Diagnosis) -> Diagnosis:
    if (diagnosis.kubectl_command or "").strip():
        return diagnosis

    pods = (investigation.get("pods") or {}).get("problematic_pods") or []
    deployments = (investigation.get("deployments") or {}).get("unhealthy_deployments") or []
    network = (investigation.get("network") or {}).get("issues") or []
    probes = (investigation.get("probes") or {}).get("failing_probes") or []

    if deployments:
        item = deployments[0]
        diagnosis.kubectl_command = (
            f"kubectl -n {item.get('namespace') or 'default'} describe deployment {item.get('name')}"
        )
        return diagnosis
    if pods:
        item = pods[0]
        ns = item.get("namespace") or "default"
        name = item.get("name")
        diagnosis.kubectl_command = (
            f"kubectl -n {ns} describe pod {name} && kubectl -n {ns} logs {name} --tail=80"
        )
        return diagnosis
    if probes:
        item = probes[0]
        ns = item.get("namespace") or "default"
        diagnosis.kubectl_command = f"kubectl -n {ns} describe pod {item.get('pod')}"
        return diagnosis
    if network:
        item = network[0]
        ns = item.get("namespace") or "default"
        diagnosis.kubectl_command = (
            f"kubectl -n {ns} get svc {item.get('service')} -o yaml && "
            f"kubectl -n {ns} get endpoints {item.get('service')} -o yaml"
        )
        return diagnosis

    diagnosis.kubectl_command = "kubectl get pods -A && kubectl get events -A --sort-by=.lastTimestamp"
    return diagnosis
