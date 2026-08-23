from fastapi import APIRouter

from app.ai.analyzer import diagnose
from app.core.config import get_settings
from app.models.schemas import HealthResponse, InvestigateRequest, InvestigateResponse
from app.services.investigation import investigate

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(status="healthy", service=settings.service_name)


@router.post("/investigate", response_model=InvestigateResponse)
def run_investigation(body: InvestigateRequest | None = None) -> InvestigateResponse:
    payload = body or InvestigateRequest()
    result = investigate(context=payload.context, namespace=payload.namespace)
    if result.status != "success":
        return result
    result.diagnosis = diagnose(result.investigation)
    return result
