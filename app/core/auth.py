import os
from datetime import datetime, timedelta

from jose import jwt
from passlib.context import CryptContext

# Загружаем логин, пароль и секретные данные из переменных окружения
SECRET_KEY = os.getenv("SECRET_KEY", "my_champion")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
ALGORITHM = os.getenv("ALGORITHM", "HS256")
USER_LOGIN = os.getenv("USER_LOGIN")
USER_PASSWORD = os.getenv("USER_PASSWORD")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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
        return False

    # Хэшируем пароль из переменной окружения и проверяем его
    hashed_password = get_hashed_password(USER_PASSWORD)
    if not verify_password(password, hashed_password):
        return False

    # Если логин и пароль верны, возвращаем пользователя
    return {"username": USER_LOGIN}


# Функция для создания JWT-токена
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # Используем значение из переменной окружения ACCESS_TOKEN_EXPIRE_MINUTES
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
