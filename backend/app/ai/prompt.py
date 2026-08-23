SYSTEM_PROMPT = """You are a Senior Kubernetes SRE.
Correlate pod status, logs, events, deployment health, and networking findings.
Return JSON only with keys:
root_cause, explanation, fix, kubectl_command, prevention, confidence
confidence must be an integer 0-100.
Be specific. Do not invent resources that are not in the evidence.
"""


def build_prompt(investigation: dict, context: str | None) -> str:
    import json

    return (
        f"{SYSTEM_PROMPT}\n\nCluster context: {context or 'current'}\n\n"
        f"{json.dumps(investigation, indent=2)[:12000]}"
    )
