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


def _create_transaction(
    client: TestClient,
    token: str,
    category_id: int,
    *,
    amount: str,
    type_: str,
    transaction_date: str,
    description: str,
) -> dict:
    response = client.post(
        TRANSACTIONS_URL,
        headers=_auth_header(token),
        json={
            "amount": amount,
            "type": type_,
            "category_id": category_id,
            "description": description,
            "transaction_date": transaction_date,
        },
    )
    assert response.status_code == 201
    return response.json()


def _seed(client: TestClient, token: str) -> dict:
    income = _create_category(client, token, "Salary", "INCOME")
    food = _create_category(client, token, "Food", "EXPENSE")
    transport = _create_category(client, token, "Transport", "EXPENSE")
    txs = {
        "salary": _create_transaction(
            client,
            token,
            income["id"],
            amount="30000.00",
            type_="INCOME",
            transaction_date="2026-08-01",
            description="salary",
        ),
        "food_early": _create_transaction(
            client,
            token,
            food["id"],
            amount="400.00",
            type_="EXPENSE",
            transaction_date="2026-08-10",
            description="food_early",
        ),
        "transport": _create_transaction(
            client,
            token,
            transport["id"],
            amount="900.00",
            type_="EXPENSE",
            transaction_date="2026-08-20",
            description="transport",
        ),
        "food_late": _create_transaction(
            client,
            token,
            food["id"],
            amount="150.00",
            type_="EXPENSE",
            transaction_date="2026-09-05",
            description="food_late",
        ),
        "food_mid": _create_transaction(
            client,
            token,
            food["id"],
            amount="250.00",
            type_="EXPENSE",
            transaction_date="2026-08-20",
            description="food_mid",
        ),
    }
    return {"income": income, "food": food, "transport": transport, "txs": txs}


def _list(client: TestClient, token: str, **params) -> dict:
    response = client.get(
        TRANSACTIONS_URL, headers=_auth_header(token), params=params
    )
    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    assert "page" in body
    assert "page_size" in body
    assert "total" in body
    assert "pages" in body
    return body


def test_list_defaults_are_paginated(client: TestClient) -> None:
    _, token = _register_and_token(client)
    _seed(client, token)
    body = _list(client, token)
    assert body["page"] == 1
    assert body["page_size"] == 20
    assert body["total"] == 5
    assert body["pages"] == 1
    assert len(body["items"]) == 5


def test_filter_by_type(client: TestClient) -> None:
    _, token = _register_and_token(client)
    _seed(client, token)
    income = _list(client, token, type="INCOME")
    expense = _list(client, token, type="EXPENSE")
    assert income["total"] == 1
    assert [item["description"] for item in income["items"]] == ["salary"]
    assert expense["total"] == 4
    assert all(item["type"] == "EXPENSE" for item in expense["items"])


def test_filter_by_category_id(client: TestClient) -> None:
    _, token = _register_and_token(client)
    seeded = _seed(client, token)
    body = _list(client, token, category_id=seeded["food"]["id"])
    assert body["total"] == 3
    assert {item["description"] for item in body["items"]} == {
        "food_early",
        "food_late",
        "food_mid",
    }


def test_filter_by_inclusive_date_range(client: TestClient) -> None:
    _, token = _register_and_token(client)
    _seed(client, token)
    body = _list(
        client,
        token,
        start_date="2026-08-10",
        end_date="2026-08-20",
    )
    assert body["total"] == 3
    assert {item["description"] for item in body["items"]} == {
        "food_early",
        "transport",
        "food_mid",
    }


def test_filter_start_date_only_and_end_date_only(client: TestClient) -> None:
    _, token = _register_and_token(client)
    _seed(client, token)
    from_september = _list(client, token, start_date="2026-09-01")
    through_august_1 = _list(client, token, end_date="2026-08-01")
    assert [item["description"] for item in from_september["items"]] == ["food_late"]
    assert [item["description"] for item in through_august_1["items"]] == ["salary"]


def test_sort_by_amount_asc_and_desc(client: TestClient) -> None:
    _, token = _register_and_token(client)
    _seed(client, token)
    asc = _list(client, token, sort_by="amount", sort_order="asc")
    desc = _list(client, token, sort_by="amount", sort_order="desc")
    asc_amounts = [Decimal(str(item["amount"])) for item in asc["items"]]
    desc_amounts = [Decimal(str(item["amount"])) for item in desc["items"]]
    assert asc_amounts == sorted(asc_amounts)
    assert desc_amounts == sorted(desc_amounts, reverse=True)
    assert [item["description"] for item in asc["items"]][0] == "food_late"
    assert [item["description"] for item in desc["items"]][0] == "salary"


def test_sort_by_transaction_date_both_directions(client: TestClient) -> None:
    _, token = _register_and_token(client)
    _seed(client, token)
    asc = _list(client, token, sort_by="transaction_date", sort_order="asc")
    desc = _list(client, token, sort_by="transaction_date", sort_order="desc")
    assert [item["description"] for item in asc["items"]][0] == "salary"
    assert [item["description"] for item in desc["items"]][0] == "food_late"
    same_day_asc = [
        item["description"]
        for item in asc["items"]
        if item["transaction_date"] == "2026-08-20"
    ]
    same_day_desc = [
        item["description"]
        for item in desc["items"]
        if item["transaction_date"] == "2026-08-20"
    ]
    assert same_day_asc == ["transport", "food_mid"]
    assert same_day_desc == ["food_mid", "transport"]


def test_pagination(client: TestClient) -> None:
    _, token = _register_and_token(client)
    _seed(client, token)
    page1 = _list(
        client,
        token,
        sort_by="amount",
        sort_order="asc",
        page=1,
        page_size=2,
    )
    page2 = _list(
        client,
        token,
        sort_by="amount",
        sort_order="asc",
        page=2,
        page_size=2,
    )
    page3 = _list(
        client,
        token,
        sort_by="amount",
        sort_order="asc",
        page=3,
        page_size=2,
    )
    assert page1["total"] == 5
    assert page1["pages"] == 3
    assert page1["page"] == 1
    assert page1["page_size"] == 2
    assert len(page1["items"]) == 2
    assert len(page2["items"]) == 2
    assert len(page3["items"]) == 1
    ids = [item["id"] for item in page1["items"] + page2["items"] + page3["items"]]
    assert len(ids) == len(set(ids))


def test_combined_filters(client: TestClient) -> None:
    _, token = _register_and_token(client)
    seeded = _seed(client, token)
    body = _list(
        client,
        token,
        type="EXPENSE",
        category_id=seeded["food"]["id"],
        start_date="2026-08-01",
        end_date="2026-08-31",
        sort_by="amount",
        sort_order="desc",
    )
    assert [item["description"] for item in body["items"]] == ["food_early", "food_mid"]
    assert body["total"] == 2


def test_empty_results(client: TestClient) -> None:
    _, token = _register_and_token(client)
    _seed(client, token)
    body = _list(client, token, start_date="2027-01-01", end_date="2027-01-31")
    assert body["items"] == []
    assert body["total"] == 0
    assert body["pages"] == 0
    assert body["page"] == 1


def test_query_isolates_other_users(client: TestClient) -> None:
    _, token_a = _register_and_token(client)
    _, token_b = _register_and_token(client)
    seeded_a = _seed(client, token_a)
    food_b = _create_category(client, token_b, "Food", "EXPENSE")
    _create_transaction(
        client,
        token_b,
        food_b["id"],
        amount="400.00",
        type_="EXPENSE",
        transaction_date="2026-08-10",
        description="other_user",
    )
    body = _list(
        client,
        token_a,
        type="EXPENSE",
        category_id=seeded_a["food"]["id"],
        start_date="2026-08-01",
        end_date="2026-08-31",
    )
    assert "other_user" not in [item["description"] for item in body["items"]]
    assert all(item["user_id"] == seeded_a["txs"]["food_early"]["user_id"] for item in body["items"])


def test_invalid_date_range(client: TestClient) -> None:
    _, token = _register_and_token(client)
    response = client.get(
        TRANSACTIONS_URL,
        headers=_auth_header(token),
        params={"start_date": "2026-09-01", "end_date": "2026-08-01"},
    )
    assert response.status_code == 422
    assert _error(response)["code"] == "INVALID_DATE_RANGE"


def test_invalid_query_parameters_rejected(client: TestClient) -> None:
    _, token = _register_and_token(client)
    invalid_type = client.get(
        TRANSACTIONS_URL,
        headers=_auth_header(token),
        params={"type": "SAVINGS"},
    )
    invalid_sort = client.get(
        TRANSACTIONS_URL,
        headers=_auth_header(token),
        params={"sort_by": "description"},
    )
    invalid_page_size = client.get(
        TRANSACTIONS_URL,
        headers=_auth_header(token),
        params={"page_size": 101},
    )
    invalid_page = client.get(
        TRANSACTIONS_URL,
        headers=_auth_header(token),
        params={"page": 0},
    )
    assert invalid_type.status_code == 422
    assert invalid_sort.status_code == 422
    assert invalid_page_size.status_code == 422
    assert invalid_page.status_code == 422
