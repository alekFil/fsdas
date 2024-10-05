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


def test_login_success(client, setup_auth_enabled):
    """Тест успешной авторизации при включенной авторизации."""
    # Проверяем, что переменная DISABLE_AUTH отключена
    assert os.getenv("DISABLE_AUTH") == "false", "Authorization should be enabled"

    response = client.post(
        "/auth/token",
        data={
            "username": os.getenv("USER_LOGIN"),
            "password": os.getenv("USER_PASSWORD"),
        },
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_fail(client, setup_auth_enabled):
    """Тест неудачной авторизации при включенной авторизации."""
    # Проверяем, что переменная DISABLE_AUTH отключена
    assert os.getenv("DISABLE_AUTH") == "false", "Authorization should be enabled"

    response = client.post(
        "/auth/token", data={"username": "wrong_user", "password": "wrong_password"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}
