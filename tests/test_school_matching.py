def test_find_school_match(client):
    # Сначала сделаем авторизацию
    auth_response = client.post(
        "/auth/token", data={"username": "@alekfil", "password": "111111"}
    )
    token = auth_response.json().get("access_token")

    # Делаем запрос на поиск совпадений
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post(
        "/data/get_school_matches",
        json={"school_name": "Звездный лед"},
        headers=headers,
    )

    assert response.status_code == 200
    matches = response.json()

    expected_matches = [
        {"id": 62, "score": 1},
        {"id": 280, "score": 0.3905392667537355},
        {"id": 111, "score": 0.3905392667537355},
        {"id": 262, "score": 0.38301276945686247},
        {"id": 25, "score": 0.3740873765058714},
    ]

    # Проверка, что количество элементов совпадает
    assert len(matches) == len(expected_matches)
