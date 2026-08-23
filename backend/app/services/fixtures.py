from copy import deepcopy

CRASHLOOP = {
    "pods": {
        "healthy": False,
        "total_pods": 1,
        "problematic_pods": [
            {"name": "payment-service-7b9c", "namespace": "demo", "phase": "Running", "status": "CrashLoopBackOff", "ready": False, "restarts": 8, "labels": {"app": "payment-service"}}
        ],
    },
    "logs": {
        "pods_checked": 1,
        "pod_logs": [
            {"pod": "payment-service-7b9c", "namespace": "demo", "status": "CrashLoopBackOff", "has_errors": True, "excerpt": "FATAL: DATABASE_URL environment variable is missing\nApplication failed during startup."}
        ],
    },
    "events": {"warning_count": 1, "detected": ["BackOff"], "findings": [{"reason": "BackOff", "type": "Warning", "message": "Back-off restarting failed container", "namespace": "demo", "object": "Pod/payment-service-7b9c", "count": 8}]},
    "deployments": {"healthy": False, "total_deployments": 1, "unhealthy_deployments": [{"name": "payment-service", "namespace": "demo", "desired": 1, "ready": 0, "available": 0, "unavailable": 1, "selector": {"app": "payment-service"}}]},
    "network": {"healthy": True, "total_services": 1, "issues": [], "dns_related": False},
}

IMAGEPULL = {
    "pods": {"healthy": False, "total_pods": 1, "problematic_pods": [{"name": "checkout-0", "namespace": "demo", "phase": "Pending", "status": "ImagePullBackOff", "ready": False, "restarts": 0, "labels": {"app": "checkout"}}]},
    "logs": {"pods_checked": 0, "pod_logs": []},
    "events": {"warning_count": 1, "detected": ["FailedPull", "ErrImagePull"], "findings": [{"reason": "FailedPull", "type": "Warning", "message": "Failed to pull image 'nginx:this-tag-does-not-exist'", "namespace": "demo", "object": "Pod/checkout-0", "count": 3}]},
    "deployments": {"healthy": False, "total_deployments": 1, "unhealthy_deployments": [{"name": "checkout", "namespace": "demo", "desired": 1, "ready": 0, "available": 0, "unavailable": 1}]},
    "network": {"healthy": True, "total_services": 1, "issues": [], "dns_related": False},
}

OOM = {
    "pods": {"healthy": False, "total_pods": 1, "problematic_pods": [{"name": "worker-0", "namespace": "demo", "phase": "Running", "status": "OOMKilled", "ready": False, "restarts": 5, "labels": {"app": "worker"}}]},
    "logs": {"pods_checked": 1, "pod_logs": [{"pod": "worker-0", "namespace": "demo", "status": "OOMKilled", "has_errors": True, "excerpt": "Killed process due to OOM"}]},
    "events": {"warning_count": 1, "detected": ["Killing"], "findings": []},
    "deployments": {"healthy": False, "total_deployments": 1, "unhealthy_deployments": [{"name": "worker", "namespace": "demo", "desired": 1, "ready": 0, "available": 0, "unavailable": 1}]},
    "network": {"healthy": True, "total_services": 0, "issues": [], "dns_related": False},
}

SELECTOR = {
    "pods": {"healthy": True, "total_pods": 1, "problematic_pods": []},
    "logs": {"pods_checked": 0, "pod_logs": []},
    "events": {"warning_count": 0, "detected": [], "findings": []},
    "deployments": {"healthy": True, "total_deployments": 1, "unhealthy_deployments": []},
    "network": {"healthy": False, "total_services": 1, "dns_related": True, "issues": [{"service": "web", "namespace": "demo", "issue": "selector_mismatch", "selector": {"app": "frontend"}, "matching_pods": []}]},
}

HEALTHY = {
    "pods": {"healthy": True, "total_pods": 3, "problematic_pods": []},
    "logs": {"pods_checked": 0, "pod_logs": []},
    "events": {"warning_count": 0, "detected": [], "findings": []},
    "deployments": {"healthy": True, "total_deployments": 2, "unhealthy_deployments": []},
    "network": {"healthy": True, "total_services": 2, "issues": [], "dns_related": False},
}


def demo_investigation(scenario: str | None = None) -> dict:
    fixtures = {"crashloop": CRASHLOOP, "imagepull": IMAGEPULL, "oom": OOM, "selector": SELECTOR, "healthy": HEALTHY}
    return deepcopy(fixtures.get((scenario or "crashloop").lower(), CRASHLOOP))
