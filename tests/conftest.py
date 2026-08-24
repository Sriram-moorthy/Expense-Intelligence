import os

import pytest
from fastapi.testclient import TestClient

_MISSING_TEST_DATABASE_URL = (
    "TEST_DATABASE_URL must be set to run tests. "
    "Point it at the local expense_intelligence PostgreSQL database, for example "
    "postgresql+psycopg://USER:PASSWORD@localhost:5432/expense_intelligence. "
    "The test suite does not load the application .env file."
)

if not os.environ.get("TEST_DATABASE_URL"):
    raise RuntimeError(_MISSING_TEST_DATABASE_URL)

os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]

from app.main import app  # noqa: E402


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
