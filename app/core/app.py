from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from sqlalchemy import text

from app.controllers.agent import router as agent_router
from app.controllers.chat_session import router as chat_session_router
from app.controllers.message import router as message_router
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

    app.add_middleware(LoggingMiddleware)
    register_exception_handlers(app)
    app.include_router(agent_router)
    app.include_router(chat_session_router)
    app.include_router(message_router)

    @app.get("/health")
    async def check_health(db: GetDB) -> dict[str, str]:
        try:
            await db.execute(text("SELECT 1"))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable") from e

        return {"status": "ok"}

    return app
