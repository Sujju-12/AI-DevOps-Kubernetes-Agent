from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException

from app.core.config import get_settings
from app.core.security import create_token, decode_token
from app.kubernetes.clusters import list_clusters
from app.models.schemas import (
    ClusterListResponse,
    HealthResponse,
    InvestigateRequest,
    InvestigateResponse,
    LoginRequest,
    LoginResponse,
)
from app.services.investigation import investigate
from app.services.store import authenticate, list_history

router = APIRouter()


def require_user(authorization: Annotated[str | None, Header()] = None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Login required")
    try:
        payload = decode_token(authorization.split(" ", 1)[1], get_settings().auth_secret)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Session expired. Please log in again.") from exc
    return str(payload.get("sub") or "user")


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="healthy", service=get_settings().service_name)


@router.post("/auth/login", response_model=LoginResponse)
def login(body: LoginRequest) -> LoginResponse:
    if not authenticate(body.username, body.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return LoginResponse(access_token=create_token({"sub": body.username}, get_settings().auth_secret), username=body.username)


@router.get("/clusters", response_model=ClusterListResponse)
def clusters(_user: str = Depends(require_user)) -> ClusterListResponse:
    return list_clusters()


@router.get("/history")
def history(_user: str = Depends(require_user)) -> dict:
    return {"items": [item.model_dump() for item in list_history()]}


@router.post("/investigate", response_model=InvestigateResponse)
async def start_investigation(
    body: InvestigateRequest,
    demo_scenario: str | None = None,
    _user: str = Depends(require_user),
) -> InvestigateResponse:
    return await investigate(context=body.context, namespace=body.namespace, demo_scenario=demo_scenario)
