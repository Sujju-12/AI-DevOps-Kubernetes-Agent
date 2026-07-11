"""API route handlers."""
from fastapi import APIRouter
from loguru import logger

router = APIRouter(prefix="/api", tags=["api"])

@router.get("/status")
async def get_status():
    """Get application status."""
    logger.info("Status endpoint called")
    return {
        "status": "operational",
        "message": "AI Kubernetes Agent is ready",
    }

@router.post("/investigate")
async def investigate_cluster():
    """Placeholder for cluster investigation endpoint."""
    logger.info("Investigate endpoint called")
    return {
        "status": "pending",
        "message": "Investigation placeholder",
        "investigation_id": "inv-001",
    }
