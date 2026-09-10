from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
CATEGORIES_URL = "/api/v1/categories"
TRANSACTIONS_URL = "/api/v1/transactions"


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


def _transaction_payload(category_id: int, **overrides) -> dict:
    payload = {
        "amount": "500.00",
        "type": "EXPENSE",
        "category_id": category_id,
        "description": "Swiggy",
        "transaction_date": "2026-08-18",
    }
    payload.update(overrides)
    return payload


def test_create_transaction_authenticated(client: TestClient) -> None:
    user, token = _register_and_token(client)
    category = _create_category(client, token, "Food", "EXPENSE")
    response = client.post(
        TRANSACTIONS_URL,
        headers=_auth_header(token),
        json=_transaction_payload(category["id"]),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == user["id"]
    assert data["category_id"] == category["id"]
    assert Decimal(str(data["amount"])) == Decimal("500.00")
    assert data["type"] == "EXPENSE"
    assert data["description"] == "Swiggy"
    assert data["transaction_date"] == "2026-08-18"


def test_unauthenticated_transaction_request_rejected(client: TestClient) -> None:
    response = client.post(
        TRANSACTIONS_URL,
        json=_transaction_payload(1),
    )
    assert response.status_code == 401
    assert _error(response)["code"] == "UNAUTHENTICATED"


def test_list_returns_only_own_transactions(client: TestClient) -> None:
    _, token_a = _register_and_token(client)
    _, token_b = _register_and_token(client)
    category_a = _create_category(client, token_a, "Food", "EXPENSE")
    category_b = _create_category(client, token_b, "Food", "EXPENSE")
    created_a = client.post(
        TRANSACTIONS_URL,
        headers=_auth_header(token_a),
        json=_transaction_payload(category_a["id"], description="A"),
    )
    created_b = client.post(
        TRANSACTIONS_URL,
        headers=_auth_header(token_b),
        json=_transaction_payload(category_b["id"], description="B"),
    )
    assert created_a.status_code == 201
    assert created_b.status_code == 201
    listed = client.get(TRANSACTIONS_URL, headers=_auth_header(token_a))
    assert listed.status_code == 200
    body = listed.json()
    assert [item["description"] for item in body["items"]] == ["A"]
    assert all(item["user_id"] == created_a.json()["user_id"] for item in body["items"])
    assert body["total"] == 1


def test_retrieve_own_transaction(client: TestClient) -> None:
    _, token = _register_and_token(client)
    category = _create_category(client, token, "Food", "EXPENSE")
    created = client.post(
        TRANSACTIONS_URL,
        headers=_auth_header(token),
        json=_transaction_payload(category["id"]),
    ).json()
    response = client.get(
        f"{TRANSACTIONS_URL}/{created['id']}",
        headers=_auth_header(token),
    )
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_cannot_retrieve_another_users_transaction(client: TestClient) -> None:
    _, token_a = _register_and_token(client)
    _, token_b = _register_and_token(client)
    category_b = _create_category(client, token_b, "Food", "EXPENSE")
    created_b = client.post(
        TRANSACTIONS_URL,
        headers=_auth_header(token_b),
        json=_transaction_payload(category_b["id"]),
    ).json()
    response = client.get(
        f"{TRANSACTIONS_URL}/{created_b['id']}",
        headers=_auth_header(token_a),
    )
    assert response.status_code == 404
    assert _error(response)["code"] == "TRANSACTION_NOT_FOUND"


def test_update_own_transaction(client: TestClient) -> None:
    _, token = _register_and_token(client)
    expense = _create_category(client, token, "Food", "EXPENSE")
    created = client.post(
        TRANSACTIONS_URL,
        headers=_auth_header(token),
        json=_transaction_payload(expense["id"]),
    ).json()
    response = client.put(
        f"{TRANSACTIONS_URL}/{created['id']}",
        headers=_auth_header(token),
        json=_transaction_payload(
            expense["id"],
            amount="750.50",
            description="Updated lunch",
        ),
    )
    assert response.status_code == 200
    data = response.json()
    assert Decimal(str(data["amount"])) == Decimal("750.50")
    assert data["description"] == "Updated lunch"
    assert data["user_id"] == created["user_id"]


def test_cannot_update_another_users_transaction(client: TestClient) -> None:
    _, token_a = _register_and_token(client)
    _, token_b = _register_and_token(client)
    category_a = _create_category(client, token_a, "Food", "EXPENSE")
    category_b = _create_category(client, token_b, "Food", "EXPENSE")
    created_b = client.post(
        TRANSACTIONS_URL,
        headers=_auth_header(token_b),
        json=_transaction_payload(category_b["id"]),
    ).json()
    response = client.put(
        f"{TRANSACTIONS_URL}/{created_b['id']}",
        headers=_auth_header(token_a),
        json=_transaction_payload(category_a["id"], description="Hijacked"),
    )
    assert response.status_code == 404
    assert _error(response)["code"] == "TRANSACTION_NOT_FOUND"
    original = client.get(
        f"{TRANSACTIONS_URL}/{created_b['id']}",
        headers=_auth_header(token_b),
    )
    assert original.json()["description"] == "Swiggy"


def test_delete_own_transaction(client: TestClient) -> None:
    _, token = _register_and_token(client)
    category = _create_category(client, token, "Food", "EXPENSE")
    created = client.post(
        TRANSACTIONS_URL,
        headers=_auth_header(token),
        json=_transaction_payload(category["id"]),
    ).json()
    response = client.delete(
        f"{TRANSACTIONS_URL}/{created['id']}",
        headers=_auth_header(token),
    )
    assert response.status_code == 204
    missing = client.get(
        f"{TRANSACTIONS_URL}/{created['id']}",
        headers=_auth_header(token),
    )
    assert missing.status_code == 404


def test_cannot_delete_another_users_transaction(client: TestClient) -> None:
    _, token_a = _register_and_token(client)
    _, token_b = _register_and_token(client)
    category_b = _create_category(client, token_b, "Food", "EXPENSE")
    created_b = client.post(
        TRANSACTIONS_URL,
        headers=_auth_header(token_b),
        json=_transaction_payload(category_b["id"]),
    ).json()
    response = client.delete(
        f"{TRANSACTIONS_URL}/{created_b['id']}",
        headers=_auth_header(token_a),
    )
    assert response.status_code == 404
    assert _error(response)["code"] == "TRANSACTION_NOT_FOUND"
    still_there = client.get(
        f"{TRANSACTIONS_URL}/{created_b['id']}",
        headers=_auth_header(token_b),
    )
    assert still_there.status_code == 200


def test_cannot_use_another_users_category(client: TestClient) -> None:
    _, token_a = _register_and_token(client)
    _, token_b = _register_and_token(client)
    category_b = _create_category(client, token_b, "Food", "EXPENSE")
    response = client.post(
        TRANSACTIONS_URL,
        headers=_auth_header(token_a),
        json=_transaction_payload(category_b["id"]),
    )
    assert response.status_code == 404
    assert _error(response)["code"] == "CATEGORY_NOT_FOUND"


def test_transaction_type_must_match_category(client: TestClient) -> None:
    _, token = _register_and_token(client)
    income = _create_category(client, token, "Salary", "INCOME")
    response = client.post(
        TRANSACTIONS_URL,
        headers=_auth_header(token),
        json=_transaction_payload(income["id"], type="EXPENSE"),
    )
    assert response.status_code == 400
    assert _error(response)["code"] == "TRANSACTION_TYPE_MISMATCH"


def test_income_and_expense_transactions(client: TestClient) -> None:
    _, token = _register_and_token(client)
    income = _create_category(client, token, "Salary", "INCOME")
    expense = _create_category(client, token, "Food", "EXPENSE")
    income_tx = client.post(
        TRANSACTIONS_URL,
        headers=_auth_header(token),
        json=_transaction_payload(
            income["id"],
            type="INCOME",
            amount="30000.00",
            description="Pay",
        ),
    )
    expense_tx = client.post(
        TRANSACTIONS_URL,
        headers=_auth_header(token),
        json=_transaction_payload(expense["id"]),
    )
    assert income_tx.status_code == 201
    assert expense_tx.status_code == 201
    assert income_tx.json()["type"] == "INCOME"
    assert expense_tx.json()["type"] == "EXPENSE"


def test_invalid_amount_and_type_validation(client: TestClient) -> None:
    _, token = _register_and_token(client)
    category = _create_category(client, token, "Food", "EXPENSE")
    zero = client.post(
        TRANSACTIONS_URL,
        headers=_auth_header(token),
        json=_transaction_payload(category["id"], amount="0"),
    )
    invalid_type = client.post(
        TRANSACTIONS_URL,
        headers=_auth_header(token),
        json=_transaction_payload(category["id"], type="SAVINGS"),
    )
    assert zero.status_code == 422
    assert invalid_type.status_code == 422


def test_description_whitespace_is_stripped(client: TestClient) -> None:
    _, token = _register_and_token(client)
    category = _create_category(client, token, "Food", "EXPENSE")
    response = client.post(
        TRANSACTIONS_URL,
        headers=_auth_header(token),
        json=_transaction_payload(category["id"], description="  lunch  "),
    )
    assert response.status_code == 201
    assert response.json()["description"] == "lunch"


def test_category_in_use_cannot_be_deleted(client: TestClient) -> None:
    _, token = _register_and_token(client)
    category = _create_category(client, token, "Food", "EXPENSE")
    created = client.post(
        TRANSACTIONS_URL,
        headers=_auth_header(token),
        json=_transaction_payload(category["id"]),
    )
    assert created.status_code == 201
    response = client.delete(
        f"{CATEGORIES_URL}/{category['id']}",
        headers=_auth_header(token),
    )
    assert response.status_code == 409
    assert _error(response)["code"] == "CATEGORY_IN_USE"
