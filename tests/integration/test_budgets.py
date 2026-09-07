from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
CATEGORIES_URL = "/api/v1/categories"
BUDGETS_URL = "/api/v1/budgets"


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


def _create_category(client: TestClient, token: str, name: str, type_: str) -> dict:
    response = client.post(
        CATEGORIES_URL,
        headers=_auth_header(token),
        json={"name": name, "type": type_},
    )
    assert response.status_code == 201
    return response.json()


def _budget_payload(category_id: int, **overrides) -> dict:
    payload = {
        "category_id": category_id,
        "amount": "5000.00",
        "month": "2026-08",
    }
    payload.update(overrides)
    return payload


def test_create_budget_authenticated(client: TestClient) -> None:
    user, token = _register_and_token(client)
    category = _create_category(client, token, "Food", "EXPENSE")
    response = client.post(
        BUDGETS_URL,
        headers=_auth_header(token),
        json=_budget_payload(category["id"]),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == user["id"]
    assert data["category_id"] == category["id"]
    assert Decimal(str(data["amount"])) == Decimal("5000.00")
    assert data["month"] == "2026-08"


def test_unauthenticated_budget_request_rejected(client: TestClient) -> None:
    response = client.post(BUDGETS_URL, json=_budget_payload(1))
    assert response.status_code == 401
    assert _error(response)["code"] == "UNAUTHENTICATED"


def test_list_returns_only_own_budgets(client: TestClient) -> None:
    _, token_a = _register_and_token(client)
    _, token_b = _register_and_token(client)
    category_a = _create_category(client, token_a, "Food", "EXPENSE")
    category_b = _create_category(client, token_b, "Food", "EXPENSE")
    created_a = client.post(
        BUDGETS_URL,
        headers=_auth_header(token_a),
        json=_budget_payload(category_a["id"]),
    )
    created_b = client.post(
        BUDGETS_URL,
        headers=_auth_header(token_b),
        json=_budget_payload(category_b["id"]),
    )
    assert created_a.status_code == 201
    assert created_b.status_code == 201
    listed = client.get(BUDGETS_URL, headers=_auth_header(token_a))
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [created_a.json()["id"]]


def test_retrieve_own_budget(client: TestClient) -> None:
    _, token = _register_and_token(client)
    category = _create_category(client, token, "Food", "EXPENSE")
    created = client.post(
        BUDGETS_URL,
        headers=_auth_header(token),
        json=_budget_payload(category["id"]),
    ).json()
    response = client.get(
        f"{BUDGETS_URL}/{created['id']}",
        headers=_auth_header(token),
    )
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]
    assert response.json()["month"] == "2026-08"


def test_cannot_retrieve_another_users_budget(client: TestClient) -> None:
    _, token_a = _register_and_token(client)
    _, token_b = _register_and_token(client)
    category_b = _create_category(client, token_b, "Food", "EXPENSE")
    created_b = client.post(
        BUDGETS_URL,
        headers=_auth_header(token_b),
        json=_budget_payload(category_b["id"]),
    ).json()
    response = client.get(
        f"{BUDGETS_URL}/{created_b['id']}",
        headers=_auth_header(token_a),
    )
    assert response.status_code == 404
    assert _error(response)["code"] == "BUDGET_NOT_FOUND"


def test_update_own_budget(client: TestClient) -> None:
    _, token = _register_and_token(client)
    category = _create_category(client, token, "Food", "EXPENSE")
    created = client.post(
        BUDGETS_URL,
        headers=_auth_header(token),
        json=_budget_payload(category["id"]),
    ).json()
    response = client.put(
        f"{BUDGETS_URL}/{created['id']}",
        headers=_auth_header(token),
        json=_budget_payload(category["id"], amount="6000.00", month="2026-09"),
    )
    assert response.status_code == 200
    data = response.json()
    assert Decimal(str(data["amount"])) == Decimal("6000.00")
    assert data["month"] == "2026-09"
    assert data["user_id"] == created["user_id"]


def test_cannot_update_another_users_budget(client: TestClient) -> None:
    _, token_a = _register_and_token(client)
    _, token_b = _register_and_token(client)
    category_a = _create_category(client, token_a, "Food", "EXPENSE")
    category_b = _create_category(client, token_b, "Food", "EXPENSE")
    created_b = client.post(
        BUDGETS_URL,
        headers=_auth_header(token_b),
        json=_budget_payload(category_b["id"]),
    ).json()
    response = client.put(
        f"{BUDGETS_URL}/{created_b['id']}",
        headers=_auth_header(token_a),
        json=_budget_payload(category_a["id"], amount="1.00"),
    )
    assert response.status_code == 404
    assert _error(response)["code"] == "BUDGET_NOT_FOUND"
    original = client.get(
        f"{BUDGETS_URL}/{created_b['id']}",
        headers=_auth_header(token_b),
    )
    assert Decimal(str(original.json()["amount"])) == Decimal("5000.00")


def test_delete_own_budget(client: TestClient) -> None:
    _, token = _register_and_token(client)
    category = _create_category(client, token, "Food", "EXPENSE")
    created = client.post(
        BUDGETS_URL,
        headers=_auth_header(token),
        json=_budget_payload(category["id"]),
    ).json()
    response = client.delete(
        f"{BUDGETS_URL}/{created['id']}",
        headers=_auth_header(token),
    )
    assert response.status_code == 204
    missing = client.get(
        f"{BUDGETS_URL}/{created['id']}",
        headers=_auth_header(token),
    )
    assert missing.status_code == 404


def test_cannot_delete_another_users_budget(client: TestClient) -> None:
    _, token_a = _register_and_token(client)
    _, token_b = _register_and_token(client)
    category_b = _create_category(client, token_b, "Food", "EXPENSE")
    created_b = client.post(
        BUDGETS_URL,
        headers=_auth_header(token_b),
        json=_budget_payload(category_b["id"]),
    ).json()
    response = client.delete(
        f"{BUDGETS_URL}/{created_b['id']}",
        headers=_auth_header(token_a),
    )
    assert response.status_code == 404
    assert _error(response)["code"] == "BUDGET_NOT_FOUND"
    still_there = client.get(
        f"{BUDGETS_URL}/{created_b['id']}",
        headers=_auth_header(token_b),
    )
    assert still_there.status_code == 200


def test_cannot_use_another_users_category_for_budget(client: TestClient) -> None:
    _, token_a = _register_and_token(client)
    _, token_b = _register_and_token(client)
    category_b = _create_category(client, token_b, "Food", "EXPENSE")
    response = client.post(
        BUDGETS_URL,
        headers=_auth_header(token_a),
        json=_budget_payload(category_b["id"]),
    )
    assert response.status_code == 404
    assert _error(response)["code"] == "CATEGORY_NOT_FOUND"


def test_budget_requires_expense_category(client: TestClient) -> None:
    _, token = _register_and_token(client)
    income = _create_category(client, token, "Salary", "INCOME")
    response = client.post(
        BUDGETS_URL,
        headers=_auth_header(token),
        json=_budget_payload(income["id"]),
    )
    assert response.status_code == 400
    assert _error(response)["code"] == "BUDGET_REQUIRES_EXPENSE_CATEGORY"


def test_duplicate_budget_conflict(client: TestClient) -> None:
    _, token = _register_and_token(client)
    category = _create_category(client, token, "Food", "EXPENSE")
    first = client.post(
        BUDGETS_URL,
        headers=_auth_header(token),
        json=_budget_payload(category["id"]),
    )
    duplicate = client.post(
        BUDGETS_URL,
        headers=_auth_header(token),
        json=_budget_payload(category["id"], amount="100.00"),
    )
    assert first.status_code == 201
    assert duplicate.status_code == 409
    error = _error(duplicate)
    assert error["code"] == "BUDGET_ALREADY_EXISTS"
    assert "integrity" not in error["message"].lower()


def test_invalid_budget_amount_and_month(client: TestClient) -> None:
    _, token = _register_and_token(client)
    category = _create_category(client, token, "Food", "EXPENSE")
    zero = client.post(
        BUDGETS_URL,
        headers=_auth_header(token),
        json=_budget_payload(category["id"], amount="0"),
    )
    bad_month = client.post(
        BUDGETS_URL,
        headers=_auth_header(token),
        json=_budget_payload(category["id"], month="August-2026"),
    )
    assert zero.status_code == 422
    assert bad_month.status_code == 422
