from app.ai.heuristics import diagnose as heuristic_diagnose
from app.ai.llm import complete_with_ollama
from app.ai.prompt import build_prompt
from app.core.config import get_settings
from app.models.schemas import Diagnosis


async def analyze_investigation(investigation: dict, context: str | None) -> Diagnosis:
    settings = get_settings()
    base = heuristic_diagnose(investigation)
    if settings.llm_provider != "ollama":
        return base

    prompt = build_prompt(investigation, context)
    llm = await complete_with_ollama(prompt)
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
    )
