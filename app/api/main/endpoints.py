from fastapi import APIRouter
from fastapi.security import OAuth2PasswordBearer

from app.services.school_matcher.school_matcher import init_school_matcher

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


# Загрузка модели и словаря при старте приложения
@router.on_event("startup")
def on_startup():
    try:
        init_school_matcher()
    except Exception as e:
        print(f"Failed to init SchoolMatcher: {e}")


# Эндпоинт для проверки статуса
@router.get("/status")
async def get_status():
    return {"status": "Приложение работает", "detail": "Все системы в норме"}
