from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from app.api.utils.auth_check import check_auth  # Импортируем глобальную проверку
from app.core.auth import authenticate_user, create_access_token

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    check_auth()  # Проверяем, нужно ли выполнять авторизацию
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
