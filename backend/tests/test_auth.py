def test_login_success(client, test_user):
    response = client.post("/api/auth/login", json={"username": "tester", "password": "secret123"})
    assert response.status_code == 200
    body = response.json()
    assert body["username"] == "tester"
    assert "id" in body


def test_login_wrong_password(client, test_user):
    response = client.post("/api/auth/login", json={"username": "tester", "password": "wrong"})
    assert response.status_code == 401


def test_login_unknown_user(client):
    response = client.post("/api/auth/login", json={"username": "nobody", "password": "whatever"})
    assert response.status_code == 401


def test_me_without_session_is_unauthenticated(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_me_with_valid_session(logged_in_client):
    response = logged_in_client.get("/api/auth/me")
    assert response.status_code == 200
    assert response.json()["username"] == "tester"


def test_logout_clears_session(logged_in_client):
    response = logged_in_client.post("/api/auth/logout")
    assert response.status_code == 200

    response = logged_in_client.get("/api/auth/me")
    assert response.status_code == 401
