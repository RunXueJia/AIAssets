async def test_login_and_current_user(client):
    response = await client.post(
        "/api/v1/auth/login", json={"username": "admin", "password": "admin123456"}
    )
    body = response.json()
    assert body["code"] == 200
    token = body["data"]["access_token"]

    current = await client.get(
        "/api/v1/auth/get_current_user", headers={"Authorization": f"Bearer {token}"}
    )
    assert current.json()["data"]["username"] == "admin"
