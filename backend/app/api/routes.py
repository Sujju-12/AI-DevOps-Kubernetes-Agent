from fastapi import APIRouter, Header

from app.ai.analyzer import diagnose
from app.core.config import get_settings
from app.models.schemas import HealthResponse, InvestigateRequest, InvestigateResponse
from app.services.history import PROGRESS_STEPS, mark_step, patch_investigation
from app.services.investigation import investigate

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(status="healthy", service=settings.service_name)


@router.post("/investigate", response_model=InvestigateResponse)
def run_investigation(
    body: InvestigateRequest | None = None,
    authorization: str | None = Header(default=None),
) -> InvestigateResponse:
    payload = body or InvestigateRequest()
    token = _bearer(authorization)
    steps = [dict(item) for item in PROGRESS_STEPS]
    if payload.investigation_id:
        patch_investigation(
            token,
            payload.investigation_id,
            {"status": "running", "steps": steps, "namespace": payload.namespace},
        )

    def on_progress(key: str) -> None:
        nonlocal steps
        steps = mark_step(token, payload.investigation_id, steps, key)

    result = investigate(
        context=payload.context,
        namespace=payload.namespace,
        on_progress=on_progress,
    )
    if result.status != "success":
        patch_investigation(
            token,
            payload.investigation_id,
            {"status": "error", "message": result.message},
        )
        return result

    on_progress("ai")
    result.diagnosis = diagnose(result.investigation)
    on_progress("done")
    diagnosis = result.diagnosis
    patch_investigation(
        token,
        payload.investigation_id,
        {
            "status": "success",
            "root_cause": diagnosis.root_cause if diagnosis else None,
            "explanation": diagnosis.explanation if diagnosis else None,
            "fix": diagnosis.fix if diagnosis else None,
            "kubectl_command": diagnosis.kubectl_command if diagnosis else None,
            "confidence": diagnosis.confidence if diagnosis else None,
            "message": result.message,
        },
    )
    return result


def _bearer(authorization: str | None) -> str | None:
    if not authorization:
        return None
    prefix = "bearer "
    if authorization.lower().startswith(prefix):
        return authorization[len(prefix) :].strip()
    return None
