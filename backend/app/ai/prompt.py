SYSTEM_PROMPT = """You are a Senior Kubernetes SRE.
Correlate pod status, logs, events, deployment health, and networking findings.
Return a practical diagnosis. Avoid vague advice.
Respond with JSON only using these keys:
root_cause, explanation, fix, kubectl_command, prevention, confidence
confidence must be an integer 0-100.
"""


def build_prompt(investigation: dict, context: str | None) -> str:
    import json

    return (
        f"{SYSTEM_PROMPT}\n\nCluster context: {context or 'current'}\n\n"
        "Investigation evidence:\n"
        f"{json.dumps(investigation, indent=2)[:12_000]}\n"
    )
