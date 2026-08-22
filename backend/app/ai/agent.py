"""AI Kubernetes agent: capture → extract issues → correlate → suggest."""

from app.ai.issues import extract_issues
from app.ai.llm import complete_with_ollama
from app.ai.prompt import build_prompt
from app.ai.recommend import suggest
from app.core.config import get_settings
from app.models.schemas import Diagnosis


def enrich_capture(capture: dict) -> dict:
    """Attach ranked issues and flat signals so the API/UI can show what was captured."""
    issues = extract_issues(capture)
    enriched = dict(capture)
    enriched["issues"] = [issue.to_dict() for issue in issues]
    enriched["signals"] = sorted({signal for issue in issues for signal in issue.signals})
    return enriched


def diagnose(capture: dict) -> Diagnosis:
    issues = extract_issues(capture)
    return suggest(issues, capture)


async def analyze_investigation(capture: dict, context: str | None) -> Diagnosis:
    """Analyze captured cluster data and optionally refine with a local Ollama model."""
    enriched = enrich_capture(capture)
    base = diagnose(enriched)
    settings = get_settings()
    if settings.llm_provider != "ollama":
        return base

    llm = await complete_with_ollama(build_prompt(enriched, context))
    if not llm:
        return base
    return Diagnosis(
        root_cause=str(llm.get("root_cause") or base.root_cause),
        explanation=str(llm.get("explanation") or base.explanation),
        fix=str(llm.get("fix") or base.fix),
        kubectl_command=str(llm.get("kubectl_command") or base.kubectl_command),
        prevention=str(llm.get("prevention") or base.prevention),
        confidence=int(llm.get("confidence") or base.confidence),
        engine="ollama",
        issue_type=base.issue_type,
        evidence=base.evidence,
    )
