def test_login_success(client):
    response = client.post(
        "/auth/token", data={"username": "@alekfil", "password": "111111"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_fail(client):
    response = client.post(
        "/auth/token", data={"username": "wrong_user", "password": "wrong_password"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}
