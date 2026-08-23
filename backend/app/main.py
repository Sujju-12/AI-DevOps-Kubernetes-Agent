from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.api.routes import router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.messages import UNEXPECTED


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    app = FastAPI(title="AI Kubernetes Agent", version="0.1.0")
    origins = [item.strip() for item in settings.cors_origins.split(",") if item.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)

    @app.exception_handler(Exception)
    async def unhandled_error(_request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled investigation error: {}", type(exc).__name__)
        return JSONResponse(status_code=500, content={"status": "error", "message": UNEXPECTED})

    return app


app = create_app()
