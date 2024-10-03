import os
import sys

# Добавляем путь к корню проекта
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as client:
        yield client
