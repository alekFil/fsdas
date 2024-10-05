from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from app.core.auth import authenticate_user, create_access_token
from app.core.logger import setup_logger

# Инициализируем логгер для auth
logger = setup_logger("auth", "app/logs/auth/logs.log")

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    logger.debug(f"Auth attempt: {form_data.username}")

    try:
        logger.info(f"Auth for user: {form_data.username}")
        user = authenticate_user(form_data.username, form_data.password)
        if not user:
            logger.warning(f"Failed auth for user: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Генерация токена при успешной аутентификации
        logger.info(f"Success auth for user: {form_data.username}")
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": user["username"]}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}

    except Exception as e:
        logger.error(f"Auth error for user: {form_data.username}, Error: {str(e)}")
        raise e
