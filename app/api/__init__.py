from fastapi import APIRouter

from .routes import v0_router

router = APIRouter()

router.include_router(v0_router)

__all__ = [router]
