import os
from datetime import datetime, timedelta, timezone

from fastapi import Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.logger import setup_logger

# Загружаем логин, пароль и секретные данные из переменных окружения
SECRET_KEY = os.getenv("SECRET_KEY", "my_champion")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
ALGORITHM = os.getenv("ALGORITHM", "HS256")
USER_LOGIN = os.getenv("USER_LOGIN")
USER_PASSWORD = os.getenv("USER_PASSWORD")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Инициализируем логгер для auth, добавляем логи в существующий файл
logger = setup_logger("auth", "app/logs/auth/logs.log")


# Функция для хэширования пароля
def get_hashed_password(password):
    return pwd_context.hash(password)


# Функция для проверки пароля
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


# Функция для аутентификации пользователя
def authenticate_user(username: str, password: str):
    # Проверяем, соответствует ли введенный логин переменной окружения
    if username != USER_LOGIN:
        logger.warning(f"Auth failed: Invalid username: {username}")
        return False

    # Хэшируем пароль из переменной окружения и проверяем его
    hashed_password = get_hashed_password(USER_PASSWORD)
    if not verify_password(password, hashed_password):
        logger.warning(f"Auth failed: Invalid password for user {username}")
        return False

    # Если логин и пароль верны, возвращаем пользователя
    logger.info(f"Auth success for user {username}")
    return {"username": USER_LOGIN}


# Функция для создания JWT-токена
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Используем значение из переменной окружения ACCESS_TOKEN_EXPIRE_MINUTES
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.info(f"JWT token created for user: {data.get('sub')}")
    return encoded_jwt


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


class AuthDependency:
    async def __call__(self, authorization: str = Header(None)):
        # Глобальная переменная для отключения авторизации (например, через переменную окружения)
        disable_auth = os.getenv("DISABLE_AUTH", "false").lower() == "true"
        logger.debug(f"disable_auth is set to {disable_auth}")

        logger.debug("AuthDependency called")

        if disable_auth:
            # Если авторизация отключена, возвращаем None, чтобы пропустить проверку
            logger.debug("Authorization is disabled, skipping auth check")
            return None

        # logger.debug(f"Received token: {token}")

        if authorization is None:
            # Если токен отсутствует, возвращаем ошибку 401
            logger.error("Token is missing")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing",
            )

        token = authorization.replace("Bearer ", "")
        logger.debug(f"Received token: {token}")

        try:
            # Декодируем JWT-токен с использованием секретного ключа
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                logger.error("Invalid token: No username in payload")
                raise HTTPException(
                    status_code=401, detail="Unauthorized: Неверный токен"
                )
            logger.debug(f"Token is valid, user: {username}")
            return username  # Возвращаем имя пользователя для дальнейшей обработки, если нужно
        except JWTError:
            # Если JWT некорректен, возвращаем ошибку 401
            logger.debug("Wrong JWT-token")
            raise HTTPException(status_code=401, detail="Unauthorized: Неверный токен")
