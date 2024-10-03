from fastapi import APIRouter

from app.api.utils.auth_check import check_auth  # Импортируем глобальную проверку
from app.services.school_matcher.school_matcher import init_school_matcher

router = APIRouter()


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
    check_auth()  # Проверяем, нужно ли выполнять авторизацию
    return {"status": "Приложение работает", "detail": "Все системы в норме"}
