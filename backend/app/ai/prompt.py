"""Build a structured Senior Kubernetes SRE prompt from investigation evidence."""

import json

SYSTEM_PROMPT = """You are a Senior Kubernetes SRE.

Your job is to troubleshoot a cluster incident using ONLY the evidence provided.
Correlate pod status, logs, events, deployment health, networking, and probes.
Do not invent cluster facts that are not in the evidence.
Be specific, practical, and beginner-friendly.
Avoid vague advice like "check the logs" unless you also say what to look for.

Return ONLY valid JSON with these keys:
{
  "root_cause": "one sentence naming the primary cause",
  "explanation": "how the evidence supports that cause",
  "fix": "practical Kubernetes fix",
  "kubectl_command": "one or more kubectl commands the operator can run",
  "prevention": "how to stop this class of failure next time",
  "confidence": 0-100 integer,
  "confidence_reason": "why the score is high or low, citing evidence"
}

If the cluster looks healthy, set root_cause to exactly:
"No critical Kubernetes issues detected. Cluster appears healthy."
Keep confidence moderate.
"""


def build_prompt(investigation: dict) -> str:
    """User message containing structured Kubernetes evidence."""
    evidence = _compact(investigation)
    return (
        "Investigate this Kubernetes incident.\n\n"
        f"## Pod Status\n{_section(evidence.get('pods'))}\n\n"
        f"## Logs\n{_section(evidence.get('logs'))}\n\n"
        f"## Events\n{_section(evidence.get('events'))}\n\n"
        f"## Deployment Health\n{_section(evidence.get('deployments'))}\n\n"
        f"## Networking Findings\n{_section(evidence.get('network'))}\n\n"
        f"## Probe Findings\n{_section(evidence.get('probes'))}\n"
    )


def build_messages(investigation: dict) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_prompt(investigation)},
    ]


def _section(value) -> str:
    if not value:
        return "(none)"
    return json.dumps(value, indent=2, default=str)[:6000]


def _compact(investigation: dict) -> dict:
    return investigation if isinstance(investigation, dict) else {}
