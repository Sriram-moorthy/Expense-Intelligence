from datetime import timedelta
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import SessionLocal
from app.models.user import User

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
ME_URL = "/api/v1/auth/me"


def _unique_user() -> dict[str, str]:
    suffix = uuid4().hex[:12]
    return {
        "username": f"user_{suffix}",
        "email": f"user_{suffix}@example.com",
        "password": "secret-password",
    }


def _error(response) -> dict:
    body = response.json()
    assert "error" in body
    assert "code" in body["error"]
    assert "message" in body["error"]
    return body["error"]


def test_register_success(client: TestClient) -> None:
    payload = _unique_user()
    response = client.post(REGISTER_URL, json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == payload["username"]
    assert data["email"] == payload["email"]
    assert "id" in data
    assert "password" not in data
    assert "password_hash" not in data


def test_register_duplicate_username(client: TestClient) -> None:
    first = _unique_user()
    second = _unique_user()
    second["username"] = first["username"]
    assert client.post(REGISTER_URL, json=first).status_code == 201
    response = client.post(REGISTER_URL, json=second)
    assert response.status_code == 409
    error = _error(response)
    assert error["code"] == "USERNAME_ALREADY_EXISTS"
    assert "integrity" not in error["message"].lower()


def test_register_duplicate_email(client: TestClient) -> None:
    first = _unique_user()
    second = _unique_user()
    second["email"] = first["email"]
    assert client.post(REGISTER_URL, json=first).status_code == 201
    response = client.post(REGISTER_URL, json=second)
    assert response.status_code == 409
    error = _error(response)
    assert error["code"] == "EMAIL_ALREADY_EXISTS"
    assert "integrity" not in error["message"].lower()


def test_register_stores_password_as_hash(client: TestClient) -> None:
    payload = _unique_user()
    response = client.post(REGISTER_URL, json=payload)
    assert response.status_code == 201
    user_id = response.json()["id"]

    db = SessionLocal()
    try:
        user = db.get(User, user_id)
        assert user is not None
        assert user.password_hash != payload["password"]
        assert verify_password(payload["password"], user.password_hash)
        assert user.password_hash.startswith("$argon2")
    finally:
        db.close()


def test_login_success(client: TestClient) -> None:
    payload = _unique_user()
    assert client.post(REGISTER_URL, json=payload).status_code == 201
    response = client.post(
        LOGIN_URL,
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert isinstance(data["access_token"], str)
    assert data["access_token"]


def test_login_invalid_password(client: TestClient) -> None:
    payload = _unique_user()
    assert client.post(REGISTER_URL, json=payload).status_code == 201
    response = client.post(
        LOGIN_URL,
        json={"email": payload["email"], "password": "wrong-password"},
    )
    assert response.status_code == 401
    error = _error(response)
    assert error["code"] == "AUTHENTICATION_FAILED"


def test_login_nonexistent_email(client: TestClient) -> None:
    payload = _unique_user()
    response = client.post(
        LOGIN_URL,
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert response.status_code == 401
    error = _error(response)
    assert error["code"] == "AUTHENTICATION_FAILED"
    invalid_password = client.post(
        LOGIN_URL,
        json={"email": payload["email"], "password": "other-password"},
    )
    assert invalid_password.json()["error"]["message"] == error["message"]


def test_me_returns_authenticated_user_only(client: TestClient) -> None:
    first = _unique_user()
    second = _unique_user()
    first_response = client.post(REGISTER_URL, json=first)
    second_response = client.post(REGISTER_URL, json=second)
    assert first_response.status_code == 201
    assert second_response.status_code == 201
    first_user = first_response.json()
    second_user = second_response.json()

    login = client.post(
        LOGIN_URL,
        json={"email": first["email"], "password": first["password"]},
    )
    token = login.json()["access_token"]
    response = client.get(ME_URL, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    me = response.json()
    assert me["id"] == first_user["id"]
    assert me["username"] == first["username"]
    assert me["email"] == first["email"]
    assert me["id"] != second_user["id"]
    assert me["username"] != second["username"]
    assert me["email"] != second["email"]
    assert "password" not in me
    assert "password_hash" not in me


def test_expired_token_is_rejected(client: TestClient) -> None:
    payload = _unique_user()
    created = client.post(REGISTER_URL, json=payload).json()
    token = create_access_token(
        str(created["id"]), expires_delta=timedelta(seconds=-1)
    )
    response = client.get(ME_URL, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert _error(response)["code"] == "UNAUTHENTICATED"


def test_invalid_token_is_rejected(client: TestClient) -> None:
    response = client.get(
        ME_URL, headers={"Authorization": "Bearer not-a-valid-token"}
    )
    assert response.status_code == 401
    assert _error(response)["code"] == "UNAUTHENTICATED"


def test_malformed_token_is_rejected(client: TestClient) -> None:
    response = client.get(ME_URL, headers={"Authorization": "Bearer a.b.c"})
    assert response.status_code == 401
    assert _error(response)["code"] == "UNAUTHENTICATED"


def test_token_for_nonexistent_user_is_rejected(client: TestClient) -> None:
    token = create_access_token("999999999")
    response = client.get(ME_URL, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert _error(response)["code"] == "UNAUTHENTICATED"


def test_missing_authorization_header_is_rejected(client: TestClient) -> None:
    response = client.get(ME_URL)
    assert response.status_code == 401
    assert _error(response)["code"] == "UNAUTHENTICATED"


def test_invalid_bearer_scheme_is_rejected(client: TestClient) -> None:
    payload = _unique_user()
    client.post(REGISTER_URL, json=payload)
    token = client.post(
        LOGIN_URL,
        json={"email": payload["email"], "password": payload["password"]},
    ).json()["access_token"]
    response = client.get(ME_URL, headers={"Authorization": f"Token {token}"})
    assert response.status_code == 401
    assert _error(response)["code"] == "UNAUTHENTICATED"


def test_hash_password_helper_uses_argon2() -> None:
    hashed = hash_password("secret-password")
    assert hashed != "secret-password"
    assert hashed.startswith("$argon2")
    assert verify_password("secret-password", hashed)
    assert not verify_password("other", hashed)
