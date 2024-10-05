import os

import pytest


@pytest.fixture
def setup_environment():
    """Устанавливает переменные окружения для включенной авторизации."""
    os.environ["SECRET_KEY"] = "your_secret_key"
    os.environ["USER_LOGIN"] = "@admin"
    os.environ["USER_PASSWORD"] = "admin"


@pytest.fixture
def setup_auth_enabled():
    """Устанавливает переменные окружения для включенной авторизации."""
    os.environ["DISABLE_AUTH"] = "false"


def test_failed_require(client, setup_auth_enabled):
    """Тест работы сервиса без токена (авторизация должна быть включена)."""
    # Проверяем, что переменная DISABLE_AUTH отключена
    assert os.getenv("DISABLE_AUTH") == "false", "Authorization should be enabled"

    # Получаем токен для авторизации
    login_response = client.post(
        "/auth/token",
        data={
            "username": os.getenv("USER_LOGIN"),
            "password": os.getenv("USER_PASSWORD"),
        },
    )
    access_token = login_response.json()["access_token"]
    print(access_token)
    # Пытаемся получить статус без токена
    response = client.get("main/status")
    assert response.status_code == 401  # Ожидаем 401, так как токен не передан


def test_status_with_token(client, setup_auth_enabled):
    """Тест работы сервиса с переданным токеном."""
    # Проверяем, что переменная DISABLE_AUTH отключена
    assert os.getenv("DISABLE_AUTH") == "false", "Authorization should be enabled"

    # Получаем токен для авторизации
    login_response = client.post(
        "/auth/token",
        data={
            "username": os.getenv("USER_LOGIN"),
            "password": os.getenv("USER_PASSWORD"),
        },
    )
    access_token = login_response.json()["access_token"]

    # Передаем токен в заголовке Authorization
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("main/status", headers=headers)
    assert response.status_code == 200  # Ожидаем успешный ответ

    # Проверяем корректный ответ сервиса
    assert response.json() == {
        "status": "Приложение работает",
        "detail": "Все системы в норме",
    }


def test_get_school_matches_requires_auth(client, setup_auth_enabled):
    """Тест работы эндпоинта /get_school_matches/ без токена (авторизация должна быть включена)."""

    # Проверяем, что переменная DISABLE_AUTH отключена
    assert os.getenv("DISABLE_AUTH") == "false", "Authorization should be enabled"

    # Получаем токен для авторизации
    login_response = client.post(
        "/auth/token",
        data={
            "username": os.getenv("USER_LOGIN"),
            "password": os.getenv("USER_PASSWORD"),
        },
    )
    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]
    print(f"Access token: {access_token}")

    # Пытаемся вызвать эндпоинт без передачи токена
    response = client.post(
        "data/get_school_matches/", json={"school_name": "Some School"}
    )

    # Ожидаем 401, так как токен не передан
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    assert response.json() == {"detail": "Token missing"}
