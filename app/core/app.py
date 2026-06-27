from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.controllers.router import router
from app.core.config import settings
from app.core.database import GetDB
from app.core.errors import register_exception_handlers
from app.core.logger import get_logger, setup_logging
from app.core.logging_middleware import LoggingMiddleware


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    setup_logging()
    logger = get_logger(__name__)
    logger.info("Application startup")
    yield
    logger.info("Application shutdown")


def create_app() -> FastAPI:
    app = FastAPI(title=settings.APP_TITLE, version=settings.APP_VERSION, lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(LoggingMiddleware)
    register_exception_handlers(app)
    app.include_router(router)

    Path(settings.AUDIO_STORAGE_DIR).mkdir(parents=True, exist_ok=True)
    app.mount("/audio", StaticFiles(directory=settings.AUDIO_STORAGE_DIR), name="audio")

    @app.get("/health")
    async def check_health(db: GetDB) -> dict[str, str]:
        try:
            await db.execute(text("SELECT 1"))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable") from e

        return {"status": "ok"}

    return app
