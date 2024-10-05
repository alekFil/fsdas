from fastapi import APIRouter, Depends

from app.core.auth import AuthDependency

router = APIRouter()

# Инициализируем зависимость для авторизации
auth_dependency = AuthDependency()


# Эндпоинт для проверки статуса
@router.get("/status")
async def get_status(token: str = Depends(auth_dependency)):
    return {"status": "Приложение работает", "detail": "Все системы в норме"}
