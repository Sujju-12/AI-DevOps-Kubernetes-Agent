from time import perf_counter

from fastapi import APIRouter, Header
from opentelemetry import trace

from app.ai.agentops import diagnose_with_metadata
from app.core.agentops_metrics import evidence_counts, record_investigation
from app.core.config import get_settings
from app.kubernetes.clusters import list_kube_contexts
from app.models.schemas import (
    ClusterListResponse,
    HealthResponse,
    InvestigateRequest,
    InvestigateResponse,
)
from app.services.history import PROGRESS_STEPS, mark_step, patch_investigation
from app.services.investigation import investigate

router = APIRouter()
tracer = trace.get_tracer("ai-kubernetes-agent")


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(status="healthy", service=settings.service_name)


@router.get("/clusters", response_model=ClusterListResponse)
def clusters() -> ClusterListResponse:
    """Return every context in the local kubeconfig (no certificate data)."""
    return list_kube_contexts()


@router.post("/investigate", response_model=InvestigateResponse)
def run_investigation(
    body: InvestigateRequest | None = None,
    authorization: str | None = Header(default=None),
) -> InvestigateResponse:
    started_at = perf_counter()
    payload = body or InvestigateRequest()
    token = _bearer(authorization)
    steps = [dict(item) for item in PROGRESS_STEPS]
    cluster_name = payload.cluster or payload.context
    if payload.investigation_id:
        patch_investigation(
            token,
            payload.investigation_id,
            {
                "status": "running",
                "steps": steps,
                "namespace": payload.namespace,
                "cluster": cluster_name,
            },
        )

    def on_progress(key: str) -> None:
        nonlocal steps
        steps = mark_step(token, payload.investigation_id, steps, key)

    with tracer.start_as_current_span("kubernetes.evidence_collection") as span:
        span.set_attribute("k8s.namespace", payload.namespace or "all")
        result = investigate(
            context=payload.context,
            namespace=payload.namespace,
            on_progress=on_progress,
        )
        span.set_attribute("investigation.status", result.status)

    if result.status != "success":
        record_investigation(
            outcome="error",
            diagnosis_source="not_run",
            duration_seconds=perf_counter() - started_at,
        )
        patch_investigation(
            token,
            payload.investigation_id,
            {"status": "error", "message": result.message},
        )
        return result

    on_progress("ai")
    with tracer.start_as_current_span("agent.diagnosis") as span:
        diagnosis, diagnosis_source = diagnose_with_metadata(result.investigation)
        result.diagnosis = diagnosis
        span.set_attribute("agent.diagnosis.available", diagnosis is not None)
        span.set_attribute("agent.diagnosis.source", diagnosis_source)
        counts = evidence_counts(result.investigation)
        span.set_attribute("agent.evidence.count", sum(counts.values()))

    record_investigation(
        outcome="success",
        diagnosis_source=diagnosis_source,
        duration_seconds=perf_counter() - started_at,
        counts=counts,
    )
    on_progress("done")
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
