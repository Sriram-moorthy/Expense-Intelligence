from sqlalchemy import inspect, text

from app.db.session import engine


def test_postgresql_connectivity() -> None:
    with engine.connect() as connection:
        assert connection.execute(text("SELECT 1")).scalar_one() == 1


def test_expected_tables_exist() -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    assert {"users", "categories", "transactions", "budgets"}.issubset(tables)


def test_primary_keys() -> None:
    inspector = inspect(engine)
    assert inspector.get_pk_constraint("users")["constrained_columns"] == ["id"]
    assert inspector.get_pk_constraint("categories")["constrained_columns"] == ["id"]
    assert inspector.get_pk_constraint("transactions")["constrained_columns"] == ["id"]
    assert inspector.get_pk_constraint("budgets")["constrained_columns"] == ["id"]


def test_foreign_keys() -> None:
    inspector = inspect(engine)

    category_fks = inspector.get_foreign_keys("categories")
    assert any(
        fk["referred_table"] == "users"
        and fk["constrained_columns"] == ["user_id"]
        and fk["referred_columns"] == ["id"]
        for fk in category_fks
    )

    transaction_fks = inspector.get_foreign_keys("transactions")
    assert any(
        fk["referred_table"] == "users"
        and fk["constrained_columns"] == ["user_id"]
        and fk["referred_columns"] == ["id"]
        for fk in transaction_fks
    )
    assert any(
        fk["referred_table"] == "categories"
        and fk["constrained_columns"] == ["category_id"]
        and fk["referred_columns"] == ["id"]
        for fk in transaction_fks
    )

    budget_fks = inspector.get_foreign_keys("budgets")
    assert any(
        fk["referred_table"] == "users"
        and fk["constrained_columns"] == ["user_id"]
        and fk["referred_columns"] == ["id"]
        for fk in budget_fks
    )
    assert any(
        fk["referred_table"] == "categories"
        and fk["constrained_columns"] == ["category_id"]
        and fk["referred_columns"] == ["id"]
        for fk in budget_fks
    )


def test_unique_constraints() -> None:
    inspector = inspect(engine)

    user_uniques = {
        tuple(uc["column_names"]) for uc in inspector.get_unique_constraints("users")
    }
    assert ("username",) in user_uniques
    assert ("email",) in user_uniques

    category_uniques = {
        tuple(uc["column_names"])
        for uc in inspector.get_unique_constraints("categories")
    }
    assert ("user_id", "name") in category_uniques

    budget_uniques = {
        tuple(uc["column_names"]) for uc in inspector.get_unique_constraints("budgets")
    }
    assert ("user_id", "category_id", "month") in budget_uniques


def test_check_constraints() -> None:
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT
                    n.nspname AS schema_name,
                    c.relname AS table_name,
                    con.conname AS constraint_name,
                    pg_get_constraintdef(con.oid) AS definition
                FROM pg_constraint con
                JOIN pg_class c ON c.oid = con.conrelid
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE con.contype = 'c'
                  AND n.nspname = 'public'
                  AND c.relname IN ('categories', 'transactions', 'budgets')
                """
            )
        ).mappings()
        by_table: dict[str, list[str]] = {}
        for row in rows:
            by_table.setdefault(row["table_name"], []).append(row["definition"])

    category_defs = " ".join(by_table.get("categories", [])).upper()
    assert "INCOME" in category_defs and "EXPENSE" in category_defs

    transaction_defs = " ".join(by_table.get("transactions", [])).upper()
    assert "AMOUNT > 0" in transaction_defs or "AMOUNT > (0)::NUMERIC" in transaction_defs
    assert "INCOME" in transaction_defs and "EXPENSE" in transaction_defs

    budget_defs = " ".join(by_table.get("budgets", [])).upper()
    assert "AMOUNT > 0" in budget_defs or "AMOUNT > (0)::NUMERIC" in budget_defs


def test_required_not_null_columns() -> None:
    inspector = inspect(engine)

    users = {col["name"]: col["nullable"] for col in inspector.get_columns("users")}
    assert users["username"] is False
    assert users["email"] is False
    assert users["password_hash"] is False
    assert users["created_at"] is False
    assert users["updated_at"] is False

    categories = {
        col["name"]: col["nullable"] for col in inspector.get_columns("categories")
    }
    assert categories["user_id"] is False
    assert categories["name"] is False
    assert categories["type"] is False
    assert categories["created_at"] is False
    assert categories["updated_at"] is False

    transactions = {
        col["name"]: col["nullable"] for col in inspector.get_columns("transactions")
    }
    assert transactions["user_id"] is False
    assert transactions["category_id"] is False
    assert transactions["amount"] is False
    assert transactions["type"] is False
    assert transactions["description"] is True
    assert transactions["transaction_date"] is False
    assert transactions["created_at"] is False
    assert transactions["updated_at"] is False

    budgets = {col["name"]: col["nullable"] for col in inspector.get_columns("budgets")}
    assert budgets["user_id"] is False
    assert budgets["category_id"] is False
    assert budgets["amount"] is False
    assert budgets["month"] is False
    assert budgets["created_at"] is False
    assert budgets["updated_at"] is False


def test_expected_indexes() -> None:
    inspector = inspect(engine)

    def index_column_sets(table: str) -> set[tuple[str, ...]]:
        return {tuple(idx["column_names"]) for idx in inspector.get_indexes(table)}

    assert ("user_id",) in index_column_sets("categories")
    assert ("user_id",) in index_column_sets("transactions")
    assert ("category_id",) in index_column_sets("transactions")
    assert ("transaction_date",) in index_column_sets("transactions")
    assert ("user_id", "transaction_date") in index_column_sets("transactions")
    assert ("user_id", "month") in index_column_sets("budgets")


def test_alembic_head_is_applied() -> None:
    from alembic.config import Config
    from alembic.runtime.migration import MigrationContext
    from alembic.script import ScriptDirectory

    alembic_cfg = Config("alembic.ini")
    script = ScriptDirectory.from_config(alembic_cfg)
    heads = script.get_heads()
    assert len(heads) == 1

    with engine.connect() as connection:
        context = MigrationContext.configure(connection)
        current = context.get_current_heads()

    assert set(current) == set(heads)
