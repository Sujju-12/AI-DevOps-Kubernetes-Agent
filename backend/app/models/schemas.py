"""Data models for the application."""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class InvestigationRequest(BaseModel):
    """Request model for cluster investigation."""
    namespace: str = "default"
    investigation_type: Optional[str] = None

class InvestigationResult(BaseModel):
    """Result model for investigation."""
    investigation_id: str
    status: str
    root_cause: str
    confidence: float
    suggested_fixes: List[Dict[str, Any]]
    timestamp: datetime

class PodStatus(BaseModel):
    """Pod status model."""
    name: str
    namespace: str
    status: str
    ready_replicas: int
    desired_replicas: int

class KubernetesEvent(BaseModel):
    """Kubernetes event model."""
    name: str
    namespace: str
    reason: str
    message: str
    timestamp: datetime
