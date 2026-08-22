"""Backend application main entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from app.core.config import settings
from app.api import routes

# Configure logger
logger.add(
    "logs/app.log",
    rotation="500 MB",
    retention="7 days",
    level=settings.LOG_LEVEL,
)

# Create FastAPI app
app = FastAPI(
    title="AI Kubernetes Troubleshooting Agent",
    description="An AI-powered platform to troubleshoot Kubernetes failures",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(routes.router)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "ai-kubernetes-agent",
    }

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AI Kubernetes Troubleshooting Agent API",
        "docs": "/docs",
        "health": "/health",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
