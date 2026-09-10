from calendar import monthrange
from datetime import date
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
CATEGORIES_URL = "/api/v1/categories"
TRANSACTIONS_URL = "/api/v1/transactions"
BUDGETS_URL = "/api/v1/budgets"
SUMMARY_URL = "/api/v1/analytics/summary"
CATEGORY_ANALYTICS_URL = "/api/v1/analytics/categories"
TRENDS_URL = "/api/v1/analytics/trends"
BUDGET_ANALYTICS_URL = "/api/v1/analytics/budgets"


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
    description: str = "item",
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


def _create_budget(
    client: TestClient, token: str, category_id: int, amount: str, month: str
) -> dict:
    response = client.post(
        BUDGETS_URL,
        headers=_auth_header(token),
        json={"category_id": category_id, "amount": amount, "month": month},
    )
    assert response.status_code == 201
    return response.json()


def _dec(value) -> Decimal:
    return Decimal(str(value))


def _seed_standard_data(client: TestClient, token: str) -> dict:
    income_cat = _create_category(client, token, "Salary", "INCOME")
    food = _create_category(client, token, "Food", "EXPENSE")
    transport = _create_category(client, token, "Transport", "EXPENSE")
    _create_transaction(
        client,
        token,
        income_cat["id"],
        amount="30000.00",
        type_="INCOME",
        transaction_date="2026-08-01",
    )
    _create_transaction(
        client,
        token,
        food["id"],
        amount="4000.00",
        type_="EXPENSE",
        transaction_date="2026-08-10",
    )
    _create_transaction(
        client,
        token,
        transport["id"],
        amount="1000.00",
        type_="EXPENSE",
        transaction_date="2026-08-20",
    )
    _create_transaction(
        client,
        token,
        food["id"],
        amount="500.00",
        type_="EXPENSE",
        transaction_date="2026-09-05",
    )
    _create_budget(client, token, food["id"], "5000.00", "2026-08")
    return {"income": income_cat, "food": food, "transport": transport}


def test_unauthenticated_analytics_rejected(client: TestClient) -> None:
    response = client.get(SUMMARY_URL)
    assert response.status_code == 401
    assert _error(response)["code"] == "UNAUTHENTICATED"


def test_summary_empty_data(client: TestClient) -> None:
    _, token = _register_and_token(client)
    response = client.get(SUMMARY_URL, headers=_auth_header(token))
    assert response.status_code == 200
    data = response.json()
    assert _dec(data["total_income"]) == Decimal("0.00")
    assert _dec(data["total_expense"]) == Decimal("0.00")
    assert _dec(data["balance"]) == Decimal("0.00")
    assert data["transaction_count"] == 0


def test_summary_overall(client: TestClient) -> None:
    _, token = _register_and_token(client)
    _seed_standard_data(client, token)
    response = client.get(SUMMARY_URL, headers=_auth_header(token))
    assert response.status_code == 200
    data = response.json()
    assert _dec(data["total_income"]) == Decimal("30000.00")
    assert _dec(data["total_expense"]) == Decimal("5500.00")
    assert _dec(data["balance"]) == Decimal("24500.00")
    assert data["transaction_count"] == 4


def test_summary_custom_and_cross_month_range(client: TestClient) -> None:
    _, token = _register_and_token(client)
    _seed_standard_data(client, token)
    august = client.get(
        SUMMARY_URL,
        headers=_auth_header(token),
        params={"start_date": "2026-08-01", "end_date": "2026-08-31"},
    )
    assert august.status_code == 200
    assert _dec(august.json()["total_expense"]) == Decimal("5000.00")
    assert august.json()["transaction_count"] == 3

    cross = client.get(
        SUMMARY_URL,
        headers=_auth_header(token),
        params={"start_date": "2026-08-15", "end_date": "2026-09-10"},
    )
    assert cross.status_code == 200
    data = cross.json()
    assert _dec(data["total_income"]) == Decimal("0.00")
    assert _dec(data["total_expense"]) == Decimal("1500.00")
    assert data["transaction_count"] == 2


def test_summary_this_month_and_last_month(client: TestClient) -> None:
    _, token = _register_and_token(client)
    income = _create_category(client, token, "Salary", "INCOME")
    food = _create_category(client, token, "Food", "EXPENSE")
    today = date.today()
    last = date(today.year - 1, 12, 1) if today.month == 1 else date(today.year, today.month - 1, 1)
    last_end = date(last.year, last.month, monthrange(last.year, last.month)[1])
    _create_transaction(
        client,
        token,
        income["id"],
        amount="1000.00",
        type_="INCOME",
        transaction_date=today.isoformat(),
    )
    _create_transaction(
        client,
        token,
        food["id"],
        amount="200.00",
        type_="EXPENSE",
        transaction_date=last_end.isoformat(),
    )

    this_month = client.get(
        SUMMARY_URL,
        headers=_auth_header(token),
        params={"period": "this_month"},
    )
    last_month = client.get(
        SUMMARY_URL,
        headers=_auth_header(token),
        params={"period": "last_month"},
    )
    assert this_month.status_code == 200
    assert last_month.status_code == 200
    assert _dec(this_month.json()["total_income"]) == Decimal("1000.00")
    assert this_month.json()["transaction_count"] == 1
    assert _dec(last_month.json()["total_expense"]) == Decimal("200.00")
    assert last_month.json()["transaction_count"] == 1


def test_summary_ignores_other_users(client: TestClient) -> None:
    _, token_a = _register_and_token(client)
    _, token_b = _register_and_token(client)
    _seed_standard_data(client, token_a)
    income_b = _create_category(client, token_b, "Salary", "INCOME")
    _create_transaction(
        client,
        token_b,
        income_b["id"],
        amount="99999.00",
        type_="INCOME",
        transaction_date="2026-08-01",
    )
    response = client.get(SUMMARY_URL, headers=_auth_header(token_a))
    assert _dec(response.json()["total_income"]) == Decimal("30000.00")
    assert response.json()["transaction_count"] == 4


def test_invalid_date_range_and_mixed_filters(client: TestClient) -> None:
    _, token = _register_and_token(client)
    inverted = client.get(
        SUMMARY_URL,
        headers=_auth_header(token),
        params={"start_date": "2026-09-01", "end_date": "2026-08-01"},
    )
    assert inverted.status_code == 422
    assert _error(inverted)["code"] == "INVALID_DATE_RANGE"

    mixed = client.get(
        SUMMARY_URL,
        headers=_auth_header(token),
        params={
            "period": "this_month",
            "start_date": "2026-08-01",
            "end_date": "2026-08-31",
        },
    )
    assert mixed.status_code == 400
    assert _error(mixed)["code"] == "INVALID_ANALYTICS_QUERY"

    partial = client.get(
        SUMMARY_URL,
        headers=_auth_header(token),
        params={"start_date": "2026-08-01"},
    )
    assert partial.status_code == 400
    assert _error(partial)["code"] == "INVALID_ANALYTICS_QUERY"


def test_category_analytics_expenses_only(client: TestClient) -> None:
    _, token = _register_and_token(client)
    seeded = _seed_standard_data(client, token)
    response = client.get(CATEGORY_ANALYTICS_URL, headers=_auth_header(token))
    assert response.status_code == 200
    items = {item["name"]: item for item in response.json()["categories"]}
    assert "Salary" not in items
    assert _dec(items["Food"]["total_expense"]) == Decimal("4500.00")
    assert items["Food"]["transaction_count"] == 2
    assert items["Food"]["category_id"] == seeded["food"]["id"]
    assert _dec(items["Transport"]["total_expense"]) == Decimal("1000.00")
    assert items["Transport"]["transaction_count"] == 1


def test_category_analytics_custom_range(client: TestClient) -> None:
    _, token = _register_and_token(client)
    _seed_standard_data(client, token)
    response = client.get(
        CATEGORY_ANALYTICS_URL,
        headers=_auth_header(token),
        params={"start_date": "2026-08-01", "end_date": "2026-08-31"},
    )
    assert response.status_code == 200
    items = {item["name"]: item for item in response.json()["categories"]}
    assert _dec(items["Food"]["total_expense"]) == Decimal("4000.00")
    assert items["Food"]["transaction_count"] == 1


def test_category_analytics_empty(client: TestClient) -> None:
    _, token = _register_and_token(client)
    response = client.get(CATEGORY_ANALYTICS_URL, headers=_auth_header(token))
    assert response.status_code == 200
    assert response.json()["categories"] == []


def test_trends_complete_monthly_history(client: TestClient) -> None:
    _, token = _register_and_token(client)
    _seed_standard_data(client, token)
    response = client.get(
        TRENDS_URL,
        headers=_auth_header(token),
        params={"group_by": "month"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["group_by"] == "month"
    by_period = {point["period"]: point for point in data["points"]}
    assert set(by_period) == {"2026-08", "2026-09"}
    assert _dec(by_period["2026-08"]["total_income"]) == Decimal("30000.00")
    assert _dec(by_period["2026-08"]["total_expense"]) == Decimal("5000.00")
    assert by_period["2026-08"]["transaction_count"] == 3
    assert _dec(by_period["2026-09"]["total_expense"]) == Decimal("500.00")
    assert by_period["2026-09"]["transaction_count"] == 1


def test_trends_group_by_day_with_range(client: TestClient) -> None:
    _, token = _register_and_token(client)
    _seed_standard_data(client, token)
    response = client.get(
        TRENDS_URL,
        headers=_auth_header(token),
        params={
            "group_by": "day",
            "start_date": "2026-08-10",
            "end_date": "2026-08-20",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["group_by"] == "day"
    by_period = {point["period"]: point for point in data["points"]}
    assert set(by_period) == {"2026-08-10", "2026-08-20"}
    assert _dec(by_period["2026-08-10"]["total_expense"]) == Decimal("4000.00")
    assert _dec(by_period["2026-08-20"]["total_expense"]) == Decimal("1000.00")


def test_trends_requires_group_by(client: TestClient) -> None:
    _, token = _register_and_token(client)
    response = client.get(TRENDS_URL, headers=_auth_header(token))
    assert response.status_code == 422


def test_budget_analytics_status_thresholds(client: TestClient) -> None:
    _, token = _register_and_token(client)
    food = _create_category(client, token, "Food", "EXPENSE")
    transport = _create_category(client, token, "Transport", "EXPENSE")
    shopping = _create_category(client, token, "Shopping", "EXPENSE")
    _create_budget(client, token, food["id"], "5000.00", "2026-08")
    _create_budget(client, token, transport["id"], "1000.00", "2026-08")
    _create_budget(client, token, shopping["id"], "1000.00", "2026-08")
    _create_transaction(
        client,
        token,
        food["id"],
        amount="2000.00",
        type_="EXPENSE",
        transaction_date="2026-08-05",
    )
    _create_transaction(
        client,
        token,
        transport["id"],
        amount="900.00",
        type_="EXPENSE",
        transaction_date="2026-08-06",
    )
    _create_transaction(
        client,
        token,
        shopping["id"],
        amount="1200.00",
        type_="EXPENSE",
        transaction_date="2026-08-07",
    )

    response = client.get(
        BUDGET_ANALYTICS_URL,
        headers=_auth_header(token),
        params={"month": "2026-08"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["month"] == "2026-08"
    by_name = {item["name"]: item for item in data["budgets"]}

    assert _dec(by_name["Food"]["budget"]) == Decimal("5000.00")
    assert _dec(by_name["Food"]["spent"]) == Decimal("2000.00")
    assert _dec(by_name["Food"]["remaining"]) == Decimal("3000.00")
    assert _dec(by_name["Food"]["percentage_used"]) == Decimal("40.00")
    assert by_name["Food"]["status"] == "UNDER_BUDGET"

    assert _dec(by_name["Transport"]["percentage_used"]) == Decimal("90.00")
    assert by_name["Transport"]["status"] == "NEAR_LIMIT"

    assert _dec(by_name["Shopping"]["spent"]) == Decimal("1200.00")
    assert _dec(by_name["Shopping"]["remaining"]) == Decimal("-200.00")
    assert by_name["Shopping"]["status"] == "OVER_BUDGET"


def test_budget_analytics_empty_and_ownership(client: TestClient) -> None:
    _, token_a = _register_and_token(client)
    _, token_b = _register_and_token(client)
    food_b = _create_category(client, token_b, "Food", "EXPENSE")
    _create_budget(client, token_b, food_b["id"], "5000.00", "2026-08")
    _create_transaction(
        client,
        token_b,
        food_b["id"],
        amount="1000.00",
        type_="EXPENSE",
        transaction_date="2026-08-01",
    )
    empty = client.get(
        BUDGET_ANALYTICS_URL,
        headers=_auth_header(token_a),
        params={"month": "2026-08"},
    )
    assert empty.status_code == 200
    assert empty.json()["budgets"] == []


def test_budget_analytics_requires_valid_month(client: TestClient) -> None:
    _, token = _register_and_token(client)
    missing = client.get(BUDGET_ANALYTICS_URL, headers=_auth_header(token))
    assert missing.status_code == 422
    invalid = client.get(
        BUDGET_ANALYTICS_URL,
        headers=_auth_header(token),
        params={"month": "August-2026"},
    )
    assert invalid.status_code == 422
    assert _error(invalid)["code"] == "INVALID_ANALYTICS_QUERY"
