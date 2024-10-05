import os

import pytest


@pytest.fixture
def setup_environment():
    """Устанавливает переменные окружения для включенной авторизации."""
    pass


@pytest.fixture
def setup_auth_disabled():
    """Устанавливает переменные окружения для отключенной авторизации."""
    os.environ["DISABLE_AUTH"] = "true"


def test_no_auth_required(client, setup_auth_disabled):
    """Тест работы сервиса без авторизации."""
    response = client.get("main/status/")
    assert response.status_code == 200
    # Добавьте проверки на корректный ответ сервиса
