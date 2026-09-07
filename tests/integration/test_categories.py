from uuid import uuid4

from fastapi.testclient import TestClient

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
CATEGORIES_URL = "/api/v1/categories"


def _unique_user() -> dict[str, str]:
    suffix = uuid4().hex[:12]
    return {
        "username": f"user_{suffix}",
        "email": f"user_{suffix}@example.com",
        "password": "secret-password",
    }


def _register_and_token(client: TestClient) -> tuple[dict, str]:
    payload = _unique_user()
    register = client.post(REGISTER_URL, json=payload)
    assert register.status_code == 201
    login = client.post(
        LOGIN_URL,
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert login.status_code == 200
    return register.json(), login.json()["access_token"]


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _error(response) -> dict:
    body = response.json()
    assert "error" in body
    assert "code" in body["error"]
    assert "message" in body["error"]
    return body["error"]


def test_create_category_authenticated(client: TestClient) -> None:
    user, token = _register_and_token(client)
    response = client.post(
        CATEGORIES_URL,
        headers=_auth_header(token),
        json={"name": "Food", "type": "EXPENSE"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Food"
    assert data["type"] == "EXPENSE"
    assert data["user_id"] == user["id"]
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_unauthenticated_category_request_rejected(client: TestClient) -> None:
    response = client.post(
        CATEGORIES_URL,
        json={"name": "Food", "type": "EXPENSE"},
    )
    assert response.status_code == 401
    assert _error(response)["code"] == "UNAUTHENTICATED"


def test_list_returns_only_own_categories(client: TestClient) -> None:
    _, token_a = _register_and_token(client)
    _, token_b = _register_and_token(client)
    created_a = client.post(
        CATEGORIES_URL,
        headers=_auth_header(token_a),
        json={"name": "Salary", "type": "INCOME"},
    )
    created_b = client.post(
        CATEGORIES_URL,
        headers=_auth_header(token_b),
        json={"name": "Rent", "type": "EXPENSE"},
    )
    assert created_a.status_code == 201
    assert created_b.status_code == 201

    listed = client.get(CATEGORIES_URL, headers=_auth_header(token_a))
    assert listed.status_code == 200
    names = [item["name"] for item in listed.json()]
    assert names == ["Salary"]
    assert all(item["user_id"] == created_a.json()["user_id"] for item in listed.json())


def test_retrieve_own_category(client: TestClient) -> None:
    _, token = _register_and_token(client)
    created = client.post(
        CATEGORIES_URL,
        headers=_auth_header(token),
        json={"name": "Transport", "type": "EXPENSE"},
    ).json()
    response = client.get(
        f"{CATEGORIES_URL}/{created['id']}",
        headers=_auth_header(token),
    )
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]
    assert response.json()["name"] == "Transport"


def test_cannot_retrieve_another_users_category(client: TestClient) -> None:
    _, token_a = _register_and_token(client)
    _, token_b = _register_and_token(client)
    created_b = client.post(
        CATEGORIES_URL,
        headers=_auth_header(token_b),
        json={"name": "Gift", "type": "INCOME"},
    ).json()
    response = client.get(
        f"{CATEGORIES_URL}/{created_b['id']}",
        headers=_auth_header(token_a),
    )
    assert response.status_code == 404
    assert _error(response)["code"] == "CATEGORY_NOT_FOUND"


def test_update_own_category(client: TestClient) -> None:
    _, token = _register_and_token(client)
    created = client.post(
        CATEGORIES_URL,
        headers=_auth_header(token),
        json={"name": "Shopping", "type": "EXPENSE"},
    ).json()
    response = client.put(
        f"{CATEGORIES_URL}/{created['id']}",
        headers=_auth_header(token),
        json={"name": "Groceries", "type": "EXPENSE"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created["id"]
    assert data["name"] == "Groceries"
    assert data["type"] == "EXPENSE"
    assert data["user_id"] == created["user_id"]


def test_cannot_update_another_users_category(client: TestClient) -> None:
    _, token_a = _register_and_token(client)
    _, token_b = _register_and_token(client)
    created_b = client.post(
        CATEGORIES_URL,
        headers=_auth_header(token_b),
        json={"name": "Bills", "type": "EXPENSE"},
    ).json()
    response = client.put(
        f"{CATEGORIES_URL}/{created_b['id']}",
        headers=_auth_header(token_a),
        json={"name": "Hijacked", "type": "INCOME"},
    )
    assert response.status_code == 404
    assert _error(response)["code"] == "CATEGORY_NOT_FOUND"
    original = client.get(
        f"{CATEGORIES_URL}/{created_b['id']}",
        headers=_auth_header(token_b),
    )
    assert original.status_code == 200
    assert original.json()["name"] == "Bills"
    assert original.json()["type"] == "EXPENSE"


def test_delete_own_category(client: TestClient) -> None:
    _, token = _register_and_token(client)
    created = client.post(
        CATEGORIES_URL,
        headers=_auth_header(token),
        json={"name": "Education", "type": "EXPENSE"},
    ).json()
    response = client.delete(
        f"{CATEGORIES_URL}/{created['id']}",
        headers=_auth_header(token),
    )
    assert response.status_code == 204
    missing = client.get(
        f"{CATEGORIES_URL}/{created['id']}",
        headers=_auth_header(token),
    )
    assert missing.status_code == 404


def test_cannot_delete_another_users_category(client: TestClient) -> None:
    _, token_a = _register_and_token(client)
    _, token_b = _register_and_token(client)
    created_b = client.post(
        CATEGORIES_URL,
        headers=_auth_header(token_b),
        json={"name": "Freelance", "type": "INCOME"},
    ).json()
    response = client.delete(
        f"{CATEGORIES_URL}/{created_b['id']}",
        headers=_auth_header(token_a),
    )
    assert response.status_code == 404
    assert _error(response)["code"] == "CATEGORY_NOT_FOUND"
    still_there = client.get(
        f"{CATEGORIES_URL}/{created_b['id']}",
        headers=_auth_header(token_b),
    )
    assert still_there.status_code == 200
    assert still_there.json()["name"] == "Freelance"


def test_duplicate_category_name_conflict(client: TestClient) -> None:
    _, token = _register_and_token(client)
    first = client.post(
        CATEGORIES_URL,
        headers=_auth_header(token),
        json={"name": "Food", "type": "EXPENSE"},
    )
    assert first.status_code == 201
    duplicate = client.post(
        CATEGORIES_URL,
        headers=_auth_header(token),
        json={"name": "Food", "type": "INCOME"},
    )
    assert duplicate.status_code == 409
    error = _error(duplicate)
    assert error["code"] == "CATEGORY_ALREADY_EXISTS"
    assert "integrity" not in error["message"].lower()


def test_income_and_expense_categories(client: TestClient) -> None:
    _, token = _register_and_token(client)
    income = client.post(
        CATEGORIES_URL,
        headers=_auth_header(token),
        json={"name": "Salary", "type": "INCOME"},
    )
    expense = client.post(
        CATEGORIES_URL,
        headers=_auth_header(token),
        json={"name": "Food", "type": "EXPENSE"},
    )
    assert income.status_code == 201
    assert expense.status_code == 201
    assert income.json()["type"] == "INCOME"
    assert expense.json()["type"] == "EXPENSE"


def test_invalid_category_type_validation(client: TestClient) -> None:
    _, token = _register_and_token(client)
    response = client.post(
        CATEGORIES_URL,
        headers=_auth_header(token),
        json={"name": "Food", "type": "SAVINGS"},
    )
    assert response.status_code == 422


def test_category_name_whitespace_is_stripped(client: TestClient) -> None:
    _, token = _register_and_token(client)
    response = client.post(
        CATEGORIES_URL,
        headers=_auth_header(token),
        json={"name": "  Food  ", "type": "EXPENSE"},
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Food"
