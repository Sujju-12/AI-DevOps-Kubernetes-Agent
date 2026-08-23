from app.ai.analyzer import diagnose as local_diagnose
from app.ai.llm import complete_with_openrouter
from app.ai.prompt import build_prompt
from app.models.schemas import Diagnosis


async def analyze_investigation(investigation: dict, context: str | None) -> Diagnosis:
    base = local_diagnose(investigation)
    llm = await complete_with_openrouter(build_prompt(investigation, context))
    if not llm:
        return base
    return Diagnosis(
        root_cause=str(llm.get("root_cause") or base.root_cause),
        explanation=str(llm.get("explanation") or base.explanation),
        fix=str(llm.get("fix") or base.fix),
        kubectl_command=str(llm.get("kubectl_command") or base.kubectl_command),
        prevention=str(llm.get("prevention") or base.prevention),
        confidence=int(llm.get("confidence") or base.confidence),
        engine="openrouter",
    )
