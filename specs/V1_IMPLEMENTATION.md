# Expense Intelligence — V1 Implementation Plan

## 1. Goal
Build a personal finance application for an individual user to manage income, expenses, categories, monthly budgets, and financial analytics.

## 2. V1 Scope
- Registration, login, logout, current-user API
- JWT authentication
- User-owned categories
- Income and expense transactions
- Monthly category budgets
- Transaction filtering, sorting, and pagination
- Financial analytics
- Validation and consistent errors
- Automated tests
- PostgreSQL + SQLAlchemy + Alembic
- Docker support

### Out of scope
Bank integrations, payment gateways, AI financial advice, receipt OCR, shared accounts, recurring transactions, notifications, and mobile apps.

## 3. Implementation Phases
1. Repository and documentation
2. FastAPI/project foundation
3. PostgreSQL, SQLAlchemy, sessions, Alembic
4. User model and authentication
5. Categories CRUD and ownership
6. Transactions CRUD and business rules
7. Transaction filtering, sorting, pagination
8. Budgets CRUD and business rules
9. Analytics
10. Testing, security and query review
11. Docker and deployment
12. README, API documentation and measured project metrics

## 4. Definition of Done
A feature is complete only when its requirement and API behavior are documented, implementation follows the architecture, validation and authorization exist, relevant tests pass, database changes have migrations, errors are defined, and unrelated scope has not been introduced.

## 5. Coding-Agent Workflow
For every Cursor task:
1. Read the relevant requirements/specs.
2. Inspect the existing code.
3. Explain the proposed plan before editing.
4. Implement only the requested scope.
5. Add/update tests.
6. Run relevant checks.
7. Report changed files and verification results.
8. Do not introduce new architecture/features without approval.

## 6. Branches
- feature/project-foundation
- feature/database-foundation
- feature/authentication
- feature/categories
- feature/transactions
- feature/transaction-querying
- feature/budgets
- feature/analytics
- feature/testing
- feature/docker

## 7. Technology
- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Pydantic / Pydantic Settings
- JWT
- pytest
- Docker
