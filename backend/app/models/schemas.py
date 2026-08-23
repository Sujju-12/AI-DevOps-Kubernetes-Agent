from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str


class InvestigateRequest(BaseModel):
    context: str | None = None
    namespace: str | None = None


class InvestigateResponse(BaseModel):
    status: str
    investigation: dict[str, Any] = Field(default_factory=dict)
    message: str | None = None
