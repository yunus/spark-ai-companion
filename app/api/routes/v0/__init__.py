from fastapi import APIRouter

from .auth import router as auth_router

router = APIRouter(prefix="/v0", tags=["v0"])

router.include_router(auth_router)

__all__ = [router]
