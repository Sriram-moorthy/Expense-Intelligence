# Expense Intelligence — V1 Database Design

## 1. Tables
V1 has four primary entities:
- users
- categories
- transactions
- budgets

Analytics are derived from transaction/budget data; no analytics table is required for V1.

## 2. users
Columns:
- id — PK
- username — required, unique
- email — required, unique
- password_hash — required
- created_at — required
- updated_at — required

Never store raw passwords.

## 3. categories
Columns:
- id — PK
- user_id — FK -> users.id
- name — required
- type — required: INCOME or EXPENSE
- created_at
- updated_at

Relationship: User 1:N Category

Constraints:
- UNIQUE(user_id, name)
- type must be INCOME or EXPENSE

## 4. transactions
Columns:
- id — PK
- user_id — FK -> users.id
- category_id — FK -> categories.id
- amount — positive NUMERIC/Decimal
- type — INCOME or EXPENSE
- description — optional
- transaction_date
- created_at
- updated_at

Relationships:
- User 1:N Transaction
- Category 1:N Transaction

Rules:
- amount > 0
- category must belong to the user
- transaction type must match category type
- financial writes must be atomic

## 5. budgets
Columns:
- id — PK
- user_id — FK -> users.id
- category_id — FK -> categories.id
- amount — positive NUMERIC/Decimal
- month — required
- created_at
- updated_at

Relationships:
- User 1:N Budget
- Category 1:N Budget

Rules:
- category must belong to the user
- category must be EXPENSE
- amount > 0
- UNIQUE(user_id, category_id, month)

## 6. Ownership
Every financial resource is scoped to its owner:
current_user.id == resource.user_id

The client must never override ownership using a supplied user_id.

## 7. Deletion
Protect historical financial data. Do not cascade-delete transactions because a category is removed. A category should not be deleted while referenced by transactions or budgets.

## 8. Indexing
Review indexes based on real access patterns. Expected candidates include:
- users.email
- users.username
- categories.user_id
- transactions.user_id
- transactions.category_id
- transactions.transaction_date
- transactions.user_id + transaction_date
- budgets.user_id + month

## 9. Money
Use PostgreSQL NUMERIC / SQLAlchemy Decimal-compatible values, not floating-point storage.

## 10. Migrations
All schema changes must be represented by Alembic migrations.
