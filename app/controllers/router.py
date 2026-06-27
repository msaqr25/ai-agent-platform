from fastapi import APIRouter

from app.controllers.agent import router as agent_router
from app.controllers.chat_session import router as session_router
from app.controllers.message import router as message_router
from app.controllers.voice import router as voice_router

router = APIRouter(prefix="/api/v1")

router.include_router(agent_router)
router.include_router(session_router)
router.include_router(message_router)
router.include_router(voice_router)
