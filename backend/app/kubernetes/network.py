def inspect_network(services: list[dict], endpoints: list[dict], pods: list[dict]) -> dict:
    endpoint_index = {}
    for item in endpoints:
        meta = item.get("metadata") or {}
        key = f"{meta.get('namespace')}/{meta.get('name')}"
        subsets = item.get("subsets") or []
        addresses = []
        for subset in subsets:
            for addr in subset.get("addresses") or []:
                addresses.append(addr.get("ip"))
        endpoint_index[key] = [ip for ip in addresses if ip]

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
        name = meta.get("name")
        namespace = meta.get("namespace")
        selector = spec.get("selector") or {}
        key = f"{namespace}/{name}"
        ready_ips = endpoint_index.get(key, [])
        matching_pods = [
            pod
            for pod in pod_labels
            if pod["namespace"] == namespace
            and selector
            and all(pod["labels"].get(k) == v for k, v in selector.items())
        ]
        if spec.get("type") == "ExternalName":
            continue
        if not selector:
            continue
        if matching_pods and not ready_ips:
            issues.append(
                {
                    "service": name,
                    "namespace": namespace,
                    "issue": "missing_endpoints",
                    "selector": selector,
                    "matching_pods": [p["name"] for p in matching_pods],
                }
            )
        elif selector and not matching_pods:
            issues.append(
                {
                    "service": name,
                    "namespace": namespace,
                    "issue": "selector_mismatch",
                    "selector": selector,
                    "matching_pods": [],
                }
            )

    dns_related = [i for i in issues if i["issue"] in {"selector_mismatch", "missing_endpoints"}]
    return {
        "healthy": len(issues) == 0,
        "total_services": len(services),
        "issues": issues,
        "dns_related": bool(dns_related),
    }
