# Expense Intelligence — V1 Architecture

## 1. Architecture

```text
Client
  ↓
Router / API Layer
  ↓
Schema / Validation
  ↓
Service Layer
  ↓
Repository Layer
  ↓
SQLAlchemy
  ↓
PostgreSQL
```

## 2. Router
Handles HTTP methods, paths, request/query data, authentication dependencies, service calls, response schemas and status codes. Routers should not contain complex business rules or direct database queries.

## 3. Schemas
Pydantic models define request DTOs, response DTOs and query-parameter models. API schemas remain separate from database models.

## 4. Services
Services contain business rules and use-case logic, such as ownership checks, transaction/category consistency, budget rules and coordination of multiple repository operations.

## 5. Repositories
Repositories encapsulate database access: queries, inserts, updates, deletes and analytics queries. They should not decide HTTP status codes.

## 6. Database
SQLAlchemy provides the engine, connection pool, ORM models, sessions and transactions. PostgreSQL stores data. Alembic manages schema migrations.

## 7. Authentication
V1 uses email/password authentication, password hashing, JWT access tokens, Bearer authentication and a current-user dependency.

## 8. Authorization
Authentication identifies the user; authorization checks whether that user can access the resource. Financial resources must be ownership-scoped.

## 9. Errors
Use consistent error responses with a machine-readable code and human-readable message.

Example:
```json
{
  "error": {
    "code": "CATEGORY_NOT_FOUND",
    "message": "Category not found"
  }
}
```

## 10. Transactions
Operations that must be atomic should run inside a database transaction and rollback on failure.

## 11. Querying
Transactions support filtering by type/category/date range, controlled sorting, ascending/descending order, and pagination. Sort fields must use an explicit allowlist.

## 12. Pagination
Use page-based pagination:
offset = (page - 1) * page_size
and database LIMIT/OFFSET with deterministic ordering.

## 13. Analytics
Analytics are derived from transactions and budgets: total income, total expenses, savings, category spending and budget usage.

## 14. Suggested Project Structure

```text
app/
├── main.py
├── api/
│   ├── dependencies.py
│   └── v1/
│       ├── router.py
│       ├── auth.py
│       ├── categories.py
│       ├── transactions.py
│       ├── budgets.py
│       └── analytics.py
├── schemas/
├── models/
├── services/
├── repositories/
├── core/
└── db/

tests/
├── unit/
└── integration/
```

## 15. Principles
- Separate responsibilities.
- Keep business rules in services.
- Keep database access in repositories.
- Keep HTTP concerns in routers.
- Never trust client-supplied ownership identifiers.
- Validate at API boundaries.
- Keep financial data isolated by user.
- Avoid premature abstractions.
