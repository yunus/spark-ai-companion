from fastapi import APIRouter

from .auth import router as auth_router
from app.api.routes.v0.ws import router as ws_router

router = APIRouter(prefix="/v0", tags=["v0"])

router.include_router(auth_router)
router.include_router(ws_router)

__all__ = [router]
