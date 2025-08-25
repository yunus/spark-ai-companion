from fastapi import APIRouter

from .chat import router as chat_router

router = APIRouter(prefix="/ws", tags=["websockets"])

router.include_router(chat_router)

__all__ = ["router"]
