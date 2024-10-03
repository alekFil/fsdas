import os

from fastapi import HTTPException

# Глобальная переменная для отключения авторизации
DISABLE_AUTH = os.getenv("DISABLE_AUTH", "false").lower() == "true"


# Зависимость для проверки авторизации
def check_auth(token: str = None):
    if DISABLE_AUTH:
        # Если авторизация отключена, просто возвращаем None
        print("PASS AUTH")
        return
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
