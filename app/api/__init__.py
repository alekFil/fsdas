from fastapi import APIRouter

from app.api.auth.endpoints import router as auth_router
from app.api.main.endpoints import router as main_router
from app.api.school_matching.endpoints import router as school_matching_router

router = APIRouter()

# Добавляем роуты из разных логических разделов
router.include_router(main_router, prefix="/main", tags=["main"])
router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(school_matching_router, prefix="/data", tags=["school_matching"])
