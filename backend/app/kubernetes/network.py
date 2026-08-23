def inspect_network(services: list[dict], endpoints: list[dict], pods: list[dict]) -> dict:
    endpoint_index = {}
    for item in endpoints:
        meta = item.get("metadata") or {}
        key = f"{meta.get('namespace')}/{meta.get('name')}"
        ips = []
        for subset in item.get("subsets") or []:
            ips.extend(addr.get("ip") for addr in subset.get("addresses") or [] if addr.get("ip"))
        endpoint_index[key] = ips

    pod_labels = [
        {
            "name": (p.get("metadata") or {}).get("name"),
            "namespace": (p.get("metadata") or {}).get("namespace"),
            "labels": (p.get("metadata") or {}).get("labels") or {},
        }
        for p in pods
    ]

    issues = []
    for svc in services:
        meta = svc.get("metadata") or {}
        spec = svc.get("spec") or {}
        if spec.get("type") == "ExternalName":
            continue
        selector = spec.get("selector") or {}
        if not selector:
            continue
        name = meta.get("name")
        namespace = meta.get("namespace")
        matching = [
            pod
            for pod in pod_labels
            if pod["namespace"] == namespace and all(pod["labels"].get(k) == v for k, v in selector.items())
        ]
        ready_ips = endpoint_index.get(f"{namespace}/{name}", [])
        if matching and not ready_ips:
            issues.append(
                {"service": name, "namespace": namespace, "issue": "missing_endpoints", "selector": selector, "matching_pods": [p["name"] for p in matching]}
            )
        elif not matching:
            issues.append(
                {"service": name, "namespace": namespace, "issue": "selector_mismatch", "selector": selector, "matching_pods": []}
            )
    return {"healthy": not issues, "total_services": len(services), "issues": issues, "dns_related": bool(issues)}
