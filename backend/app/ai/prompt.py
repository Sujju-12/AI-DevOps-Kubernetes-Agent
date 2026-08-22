SYSTEM_PROMPT = """You are a Senior Kubernetes SRE.
You receive already-extracted issues plus supporting evidence (pod status, logs, events, networking).
Correlate those signals. Do not invent resources that are not in the evidence.
Return JSON only with keys:
root_cause, explanation, fix, kubectl_command, prevention, confidence
confidence must be an integer 0-100.
Prefer the highest-severity extracted issue.
"""


def build_prompt(investigation: dict, context: str | None) -> str:
    import json

    payload = {
        "cluster_context": context or "current",
        "issues": investigation.get("issues") or [],
        "signals": investigation.get("signals") or [],
        "pods": investigation.get("pods") or {},
        "logs": investigation.get("logs") or {},
        "events": investigation.get("events") or {},
        "network": investigation.get("network") or {},
        "deployments": investigation.get("deployments") or {},
    }
    return SYSTEM_PROMPT + "\n\n" + json.dumps(payload, indent=2)[:12_000]
