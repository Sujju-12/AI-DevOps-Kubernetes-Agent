import asyncio
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse
from loguru import logger

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
from app.services.progress import progress_bus
from app.services.store import authenticate, list_history

router = APIRouter()


def require_user(authorization: Annotated[str | None, Header()] = None) -> str:
    settings = get_settings()
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Login required")
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_token(token, settings.auth_secret)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Session expired. Please log in again.") from exc
    return str(payload.get("sub") or "user")


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(status="healthy", service=settings.service_name, mode="local")


@router.post("/auth/login", response_model=LoginResponse)
def login(body: LoginRequest) -> LoginResponse:
    settings = get_settings()
    if not authenticate(body.username, body.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_token({"sub": body.username}, settings.auth_secret)
    return LoginResponse(access_token=token, username=body.username)


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
    job_id = str(uuid.uuid4())
    return await investigate(
        context=body.context,
        namespace=body.namespace,
        job_id=job_id,
        demo_scenario=demo_scenario,
    )


@router.post("/investigate/jobs")
async def create_job(
    body: InvestigateRequest,
    demo_scenario: str | None = None,
    _user: str = Depends(require_user),
) -> dict:
    job_id = str(uuid.uuid4())

    async def _run() -> None:
        try:
            await investigate(
                context=body.context,
                namespace=body.namespace,
                job_id=job_id,
                demo_scenario=demo_scenario,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Background investigation failed: {}", exc)

    asyncio.create_task(_run())
    return {"job_id": job_id, "status": "started", "context": body.context}


@router.get("/investigate/{job_id}/events")
async def investigation_events(job_id: str, _user: str = Depends(require_user)) -> StreamingResponse:
    queue = progress_bus.subscribe(job_id)

    async def stream():
        while True:
            event = await queue.get()
            yield progress_bus.encode(event)
            if event.get("event") in {"result", "error"}:
                break

    return StreamingResponse(stream(), media_type="text/event-stream")
