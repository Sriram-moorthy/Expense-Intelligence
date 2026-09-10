from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_openapi_docs_available(client: TestClient) -> None:
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_schema_includes_v1_paths(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/health" in paths
    assert "/api/v1/auth/register" in paths
    assert "/api/v1/auth/login" in paths
    assert "/api/v1/auth/me" in paths

    assert "/api/v1/categories" in paths
    assert "/api/v1/categories/{category_id}" in paths
    assert "post" in paths["/api/v1/categories"]
    assert "get" in paths["/api/v1/categories"]
    assert "get" in paths["/api/v1/categories/{category_id}"]
    assert "put" in paths["/api/v1/categories/{category_id}"]
    assert "delete" in paths["/api/v1/categories/{category_id}"]

    assert "/api/v1/transactions" in paths
    assert "/api/v1/transactions/{transaction_id}" in paths
    assert "post" in paths["/api/v1/transactions"]
    assert "get" in paths["/api/v1/transactions"]
    list_params = {
        param["name"]
        for param in paths["/api/v1/transactions"]["get"].get("parameters", [])
    }
    assert {
        "type",
        "category_id",
        "start_date",
        "end_date",
        "sort_by",
        "sort_order",
        "page",
        "page_size",
    }.issubset(list_params)
    assert "get" in paths["/api/v1/transactions/{transaction_id}"]
    assert "put" in paths["/api/v1/transactions/{transaction_id}"]
    assert "delete" in paths["/api/v1/transactions/{transaction_id}"]

    assert "/api/v1/budgets" in paths
    assert "/api/v1/budgets/{budget_id}" in paths
    assert "post" in paths["/api/v1/budgets"]
    assert "get" in paths["/api/v1/budgets"]
    assert "get" in paths["/api/v1/budgets/{budget_id}"]
    assert "put" in paths["/api/v1/budgets/{budget_id}"]
    assert "delete" in paths["/api/v1/budgets/{budget_id}"]

    assert "/api/v1/analytics/summary" in paths
    assert "/api/v1/analytics/categories" in paths
    assert "/api/v1/analytics/trends" in paths
    assert "/api/v1/analytics/budgets" in paths
    assert "get" in paths["/api/v1/analytics/summary"]
    assert "get" in paths["/api/v1/analytics/categories"]
    assert "get" in paths["/api/v1/analytics/trends"]
    assert "get" in paths["/api/v1/analytics/budgets"]
