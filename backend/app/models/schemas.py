from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str
    mode: str = "local"


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


class ClusterContext(BaseModel):
    name: str
    cluster: str
    user: str = ""
    namespace: str | None = None
    server: str | None = None
    is_current: bool = False


class ClusterListResponse(BaseModel):
    kubeconfig_path: str
    current_context: str | None = None
    contexts: list[ClusterContext] = Field(default_factory=list)
    warning: str | None = None


class InvestigateRequest(BaseModel):
    context: str | None = None
    namespace: str | None = None


class Diagnosis(BaseModel):
    root_cause: str
    explanation: str
    fix: str
    kubectl_command: str
    prevention: str = ""
    confidence: int = 0
    engine: str = "heuristic"
    issue_type: str = ""
    evidence: list[str] = Field(default_factory=list)


class InvestigationRecord(BaseModel):
    id: str
    timestamp: str
    context: str | None = None
    namespace: str | None = None
    root_cause: str
    confidence: int
    status: str


class InvestigateResponse(BaseModel):
    status: str
    job_id: str
    cluster_context: str | None = None
    investigation: dict[str, Any] = Field(default_factory=dict)
    diagnosis: Diagnosis | None = None
    error: str | None = None
    history: list[InvestigationRecord] = Field(default_factory=list)
