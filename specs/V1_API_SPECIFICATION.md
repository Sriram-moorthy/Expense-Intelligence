# Expense Intelligence — V1 API Specification

## 1. Base Path
`/api/v1`

## 2. Authentication
Protected endpoints use:
`Authorization: Bearer <JWT>`

Missing/invalid authentication returns 401.

## 3. Authentication
- `POST /api/v1/auth/register` — create account, 201
- `POST /api/v1/auth/login` — authenticate and return access token
- `POST /api/v1/auth/logout` — authenticated logout; token strategy finalized during implementation
- `GET /api/v1/auth/me` — current authenticated user

## 4. Categories
- `POST /api/v1/categories` — create
- `GET /api/v1/categories` — list current user's categories
- `GET /api/v1/categories/{id}` — get one
- `PATCH /api/v1/categories/{id}` — update
- `DELETE /api/v1/categories/{id}` — delete

Create request:
```json
{
  "name": "Food",
  "type": "EXPENSE"
}
```

Rules:
- type is INCOME or EXPENSE
- name is required
- name is unique per user
- user ownership is derived from JWT

## 5. Transactions
- `POST /api/v1/transactions` — create, 201
- `GET /api/v1/transactions` — list
- `GET /api/v1/transactions/{id}` — get one
- `PATCH /api/v1/transactions/{id}` — update
- `DELETE /api/v1/transactions/{id}` — delete

Create request:
```json
{
  "amount": 500.00,
  "type": "EXPENSE",
  "category_id": 3,
  "description": "Swiggy",
  "transaction_date": "2026-08-18"
}
```

Server-owned fields such as id, user_id and timestamps are not supplied by the client.

### Transaction query parameters
- `type`
- `category_id`
- `from`
- `to`
- `sort_by`
- `order`
- `page`
- `page_size`

Example:
```text
GET /api/v1/transactions?type=EXPENSE&category_id=3&from=2026-08-01&to=2026-08-31&sort_by=amount&order=desc&page=1&page_size=20
```

Filtering uses AND semantics. Sorting uses an explicit allowlist. Pagination uses:
`offset = (page - 1) * page_size`

## 6. Budgets
- `POST /api/v1/budgets` — create, 201
- `GET /api/v1/budgets` — list
- `GET /api/v1/budgets/{id}` — get one
- `PATCH /api/v1/budgets/{id}` — update
- `DELETE /api/v1/budgets/{id}` — delete

Create request:
```json
{
  "category_id": 3,
  "amount": 5000,
  "month": "2026-08"
}
```

Rules:
- category belongs to current user
- category must be EXPENSE
- one budget per user/category/month

## 7. Analytics
- `GET /api/v1/analytics/summary`
- `GET /api/v1/analytics/categories`
- `GET /api/v1/analytics/budgets`

Summary example:
```json
{
  "total_income": 30000,
  "total_expenses": 12500,
  "net_savings": 17500
}
```

Analytics must be scoped to the authenticated user.

## 8. Status Codes
- 200 — successful read/update
- 201 — created
- 204 — successful deletion with no body
- 400 — invalid operation where applicable
- 401 — unauthenticated
- 403 — explicitly forbidden where applicable
- 404 — not found / ownership-isolated resource
- 409 — conflict such as duplicate category/budget
- 422 — validation error
- 500 — unexpected server error

## 9. API Principles
- Resource-oriented URLs
- HTTP methods express operations
- Query parameters for filtering, sorting and pagination
- Separate request/response schemas from database models
- Consistent errors
- Validate all external input
- Never accept client-supplied user_id for ownership
