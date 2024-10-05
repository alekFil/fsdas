import os
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.auth import AuthDependency  # Импортируем зависимость
from app.core.database import DatabaseConnection
from app.core.logger import setup_logger
from app.services.school_matcher.school_matcher import SchoolMatcher

# Инициализируем логгер для school_matching
logger = setup_logger("school_matching", "app/logs/school_matcher/logs.log")


class SchoolRequest(BaseModel):
    school_name: str


class MatchResponse(BaseModel):
    id: Optional[int]
    score: float


router = APIRouter()

# Настраиваем OAuth2PasswordBearer, чтобы получить токен
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
auth_dependency = AuthDependency()  # Инициализируем зависимость

DATABASE_URL = os.getenv("DATABASE_URL")
db = DatabaseConnection(DATABASE_URL)
engine = db.get_engine()
school_marcher = SchoolMatcher(engine)


@router.post("/get_school_matches/", response_model=List[MatchResponse])
def get_school_matches(
    request: SchoolRequest,
    token: str = Depends(auth_dependency),
) -> List[MatchResponse]:
    """
    Функция для нахождения соответствие названия школы записи в базе данных.
    Возвращает список id наиболее вероятных совпадений, от большего
    к меньшему

    - **school_name**: str, название школы и регион, разделенные запятой

    Example response:
    [
        {
            "id":1842,
            "score":0.7336769261592321,
        },
        {
            "id":206,
            "score":0.7336769261592321,
        },
        {
            "id":218,
            "score":0.7336769261592321,
        },
        {
            "id":219,
            "score":0.7336769261592321,
        },
        {
            "id":220,
            "score":0.7336769261592321,
        },
    ]
    """
    logger.info(f"Received request for school matches: {request.school_name}")
    logger.debug(f"Token: {token}")

    matches = school_marcher.find_school_match(request.school_name)
    if matches:
        logger.info(f"Matches found for school {request.school_name}: {matches}")
        return matches
    else:
        logger.warning(f"No matches found for school {request.school_name}")
        raise HTTPException(status_code=404, detail="Matches not found")


@router.post("/reload_resources/")
def reload_resources(token: str = Depends(auth_dependency)):
    """
    Эндпоинт для обновления ресурсов SchoolMatcher.
    """
    logger.info("Starting resource reload")
    school_marcher.create_resources()
    school_marcher.load_resources()
    logger.info("Resources reloaded successfully")
    return {"message": "Ресурсы успешно обновлены"}
