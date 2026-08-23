from fastapi import APIRouter

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
    return investigate(context=payload.context, namespace=payload.namespace)
