def test_status(client):
    response = client.get("/main/status")
    assert response.status_code == 200
    assert response.json() == {
        "status": "Приложение работает",
        "detail": "Все системы в норме",
    }
