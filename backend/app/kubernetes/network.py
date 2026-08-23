def inspect_network(
    services: list[dict] | None = None,
    endpoints: list[dict] | None = None,
    pods: list[dict] | None = None,
    events: list[dict] | None = None,
) -> dict:
    """Check service existence, selectors, missing endpoints, and DNS-related events."""
    services = services or []
    endpoints = endpoints or []
    pods = pods or []
    events = events or []

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
                {
                    "service": name,
                    "namespace": namespace,
                    "issue": "missing_endpoints",
                    "selector": selector,
                    "matching_pods": [p["name"] for p in matching],
                }
            )
        elif not matching:
            issues.append(
                {
                    "service": name,
                    "namespace": namespace,
                    "issue": "selector_mismatch",
                    "selector": selector,
                    "matching_pods": [],
                }
            )

    dns_findings = []
    for item in events:
        message = (item.get("message") or "")
        reason = item.get("reason") or ""
        blob = f"{reason} {message}".lower()
        if any(token in blob for token in ("dns", "coredns", "nxdomain", "servicecidr")):
            obj = item.get("involvedObject") or {}
            dns_findings.append(
                {
                    "reason": reason,
                    "message": message[:400],
                    "object": f"{obj.get('kind', 'Object')}/{obj.get('name', 'unknown')}",
                }
            )

    listed = [
        {
            "name": (svc.get("metadata") or {}).get("name"),
            "namespace": (svc.get("metadata") or {}).get("namespace"),
            "type": (svc.get("spec") or {}).get("type") or "ClusterIP",
        }
        for svc in services
    ]

    return {
        "healthy": not issues and not dns_findings,
        "total_services": len(services),
        "services": listed[:50],
        "issues": issues,
        "dns_related": dns_findings[:15],
    }
