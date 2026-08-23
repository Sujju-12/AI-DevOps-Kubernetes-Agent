from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str


class InvestigateRequest(BaseModel):
    context: str | None = None
    namespace: str | None = None
    investigation_id: str | None = None


class Diagnosis(BaseModel):
    root_cause: str
    explanation: str
    fix: str
    kubectl_command: str
    prevention: str = ""
    confidence: int = 0
    confidence_reason: str = ""


class InvestigateResponse(BaseModel):
    status: str
    investigation: dict[str, Any] = Field(default_factory=dict)
    diagnosis: Diagnosis | None = None
    message: str | None = None
