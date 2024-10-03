import os
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from app.core.database import DatabaseConnection
from app.services.school_matcher.school_matcher import SchoolMatcher


class SchoolRequest(BaseModel):
    school_name: str


class MatchResponse(BaseModel):
    id: Optional[int]
    score: float


router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

DATABASE_URL = os.getenv("DATABASE_URL")
db = DatabaseConnection(DATABASE_URL)
engine = db.get_engine()
school_marcher = SchoolMatcher(engine)


@router.post("/get_school_matches/", response_model=List[MatchResponse])
def get_school_matches(
    request: SchoolRequest,
    token: str = Depends(oauth2_scheme),
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
    matches = school_marcher.find_school_match(request.school_name)
    if matches:
        return matches
    else:
        raise HTTPException(status_code=404, detail="Matches not found")


@router.post("/reload_resources/")
def reload_resources(token: str = Depends(oauth2_scheme)):
    """
    Эндпоинт для обновления ресурсов SchoolMatcher.
    """
    school_marcher.create_resources()
    school_marcher.load_resources()
    return {"message": "Ресурсы успешно обновлены"}
