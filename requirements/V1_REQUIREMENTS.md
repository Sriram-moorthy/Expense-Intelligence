# Expense Intelligence — V1 Requirements

## 1. Problem Statement

Expense Intelligence is a personal finance application that allows individuals to record income and expenses, organize transactions into categories, set spending budgets, and monitor their financial activity through analytics.

The goal of V1 is to provide a simple, reliable foundation for tracking personal finances.

---

## 2. Target User

**Individual user**

V1 supports a single type of user: an individual managing their own personal financial data.

---

## 3. Goals

Expense Intelligence should enable users to:

1. Record their income and expenses.
2. Organize financial transactions using categories.
3. Set monthly spending budgets for categories.
4. Track actual spending against budgets.
5. View financial summaries and spending breakdowns for a selected date range.
6. Keep personal financial data private and isolated from other users.

---

# 4. Functional Requirements

## 4.1 Authentication

### FR-AUTH-01
The system shall allow a user to create an account using a username, email, and password.

### FR-AUTH-02
The system shall allow a registered user to log in using their email and password.

### FR-AUTH-03
The system shall allow an authenticated user to log out.

### FR-AUTH-04
The system shall allow an authenticated user to retrieve their profile.

---

## 4.2 Transactions

A transaction represents an actual movement of money.

A transaction can be either an **INCOME** or an **EXPENSE**.

### FR-TRANS-01
The system shall allow an authenticated user to create an income or expense transaction.

### FR-TRANS-02
The system shall allow an authenticated user to view their transactions.

### FR-TRANS-03
The system shall allow an authenticated user to retrieve an individual transaction.

### FR-TRANS-04
The system shall allow an authenticated user to update their transaction.

### FR-TRANS-05
The system shall allow an authenticated user to delete their transaction.

### FR-TRANS-06
The system shall allow an authenticated user to filter transactions by category, transaction type, and date range.

### FR-TRANS-07
The system shall allow an authenticated user to sort transactions by date and amount.

### FR-TRANS-08
The system shall associate an expense transaction with an appropriate expense category.

### FR-TRANS-09
The system shall associate an income transaction with an appropriate income category when income categories are used.

---

## 4.3 Categories

A category represents the classification of a transaction.

V1 supports separate categories for income and expenses.

Examples:

**Expense categories**
- Food
- Transport
- Shopping
- Education
- Bills

**Income categories**
- Salary
- Freelance
- Gift

### FR-CAT-01
The system shall allow an authenticated user to create a category.

### FR-CAT-02
The system shall allow an authenticated user to view their categories.

### FR-CAT-03
The system shall allow an authenticated user to retrieve an individual category.

### FR-CAT-04
The system shall allow an authenticated user to update a category.

### FR-CAT-05
The system shall allow an authenticated user to delete a category.

### FR-CAT-06
The system shall associate each category with a category type indicating whether it is intended for income or expenses.

---

## 4.4 Budgets

A budget represents the amount a user plans to spend for a category during a specific period.

For V1:

- Budgets are monthly.
- A user can have only one budget for a specific category in a specific month.

Example:

```text
Food
Budget: ₹5,000
Month: August 2026
```

### FR-BUDGET-01
The system shall allow an authenticated user to create a monthly spending budget for a category.

### FR-BUDGET-02
The system shall allow an authenticated user to view their budgets.

### FR-BUDGET-03
The system shall allow an authenticated user to retrieve an individual budget.

### FR-BUDGET-04
The system shall allow an authenticated user to update their budget.

### FR-BUDGET-05
The system shall allow an authenticated user to delete their budget.

### FR-BUDGET-06
The system shall associate each budget with a specific category and month.

### FR-BUDGET-07
The system shall prevent a user from creating more than one budget for the same category in the same month.

### FR-BUDGET-08
The system shall calculate the amount spent against a category budget based on the user's expense transactions for that category and month.

### FR-BUDGET-09
The system shall calculate the remaining budget amount.

Example:

```text
Budget:    ₹5,000
Spent:     ₹3,500
Remaining: ₹1,500
```

---

## 4.5 Analytics

Analytics provide the user with a summary of their financial activity for a selected date range.

### FR-ANALYTICS-01
The system shall allow an authenticated user to view total income for a specified date range.

### FR-ANALYTICS-02
The system shall allow an authenticated user to view total expenses for a specified date range.

### FR-ANALYTICS-03
The system shall calculate net savings for a specified date range.

```text
Net Savings = Total Income - Total Expenses
```

### FR-ANALYTICS-04
The system shall allow an authenticated user to view expenses grouped by category for a specified date range.

### FR-ANALYTICS-05
The system shall allow an authenticated user to view budget usage for a specified month.

Example:

```text
Food
Budget:   ₹5,000
Spent:    ₹4,200
Usage:    84%
Remaining: ₹800
```

---

## 4.6 Data Consistency

### FR-DATA-01
When a transaction is created, updated, or deleted, the system shall ensure that category spending, budget usage, and analytics calculations reflect the latest transaction data.

---

# 5. Non-Functional Requirements

## 5.1 Security

### NFR-SEC-01
All protected operations shall require authentication.

### NFR-SEC-02
An authenticated user shall only be able to access and modify their own financial data.

### NFR-SEC-03
Passwords shall not be stored in plaintext.

---

## 5.2 Data Integrity

### NFR-DATA-01
Transaction operations shall maintain database consistency and shall not leave partially completed data when an operation fails.

### NFR-DATA-02
The database shall enforce appropriate constraints to maintain valid relationships between users, transactions, categories, and budgets.

---

## 5.3 Performance

### NFR-PERF-01
The system should provide responsive API performance for normal user operations under the expected V1 workload.

Performance targets will be established later through load testing and benchmarking.

---

## 5.4 Maintainability

### NFR-MAINT-01
The application shall use a modular architecture that separates API handling, business logic, data access, and database models.

The intended high-level flow is:

```text
API Layer
    ↓
Service Layer
    ↓
Repository / Data Access Layer
    ↓
Database
```

---

## 5.5 Reliability

### NFR-REL-01
The system shall handle expected validation and database errors without exposing sensitive implementation details to users.

### NFR-REL-02
Failed operations shall not leave the system in an inconsistent state.

---

# 6. MVP Scope

The V1 MVP includes:

### Authentication
- User registration
- Login
- Logout
- Current user/profile

### Transactions
- Create income/expense
- List transactions
- Retrieve a transaction
- Update transaction
- Delete transaction
- Filter transactions
- Sort transactions

### Categories
- Create category
- List categories
- Retrieve category
- Update category
- Delete category
- Income/expense category types

### Budgets
- Create monthly category budget
- List budgets
- Retrieve budget
- Update budget
- Delete budget
- Budget usage calculation
- Remaining budget calculation

### Analytics
- Total income
- Total expenses
- Net savings
- Category-wise expense breakdown
- Monthly budget usage

---

# 7. Out of Scope for V1

The following features will not be implemented in the initial MVP:

- AI-powered transaction categorization
- AI-generated financial recommendations
- Natural-language financial queries
- RAG
- CSV/bank statement import
- Automatic bank integration
- Redis caching
- Celery/background workers
- Email notifications
- Push notifications
- Recurring transactions
- Investment tracking
- Mobile application
- Multi-user organizations
- Microservices
- Kubernetes
- Advanced forecasting
- Production cloud deployment

These features may be introduced in later versions after the V1 backend foundation is stable.

---

# 8. V1 Business Rules

### BR-01 — Transaction Type
Every transaction must be either `INCOME` or `EXPENSE`.

### BR-02 — Category Type
A category must indicate whether it is intended for `INCOME` or `EXPENSE`.

### BR-03 — Category Matching
An expense transaction should use an expense category, and an income transaction should use an income category.

### BR-04 — Budget Type
A budget can only be created for an expense category.

### BR-05 — Monthly Budget Uniqueness
A user can have only one budget for a particular category in a particular month.

### BR-06 — Budget Spending
Budget spending is calculated from expense transactions belonging to the budget's category and month.

### BR-07 — Financial Ownership
Every user's financial data belongs to that user and must be isolated from other users.

### BR-08 — Analytics
Analytics are calculated from the user's transactions and must reflect the latest transaction data.

---

# 9. V1 Success Criteria

V1 is considered complete when an authenticated user can successfully:

1. Create an account and log in.
2. Create income and expense categories.
3. Record income and expenses.
4. View, filter, sort, update, and delete transactions.
5. Create monthly budgets for expense categories.
6. View budget usage and remaining amounts.
7. View income, expenses, savings, and category-wise spending for a selected date range.
8. Access only their own financial data.
9. Perform these operations without leaving inconsistent database state.

---

# 10. Future Evolution

After V1, the system can evolve progressively:

```text
V1
Backend Foundation
    ↓
V2
Testing + Database Optimization
    ↓
V3
Redis + Caching
    ↓
V4
CSV Import + Background Processing
    ↓
V5
Notifications + Scheduled Jobs
    ↓
V6
Docker + CI/CD
    ↓
V7
Observability + Cloud Deployment
    ↓
V8
AI Transaction Categorization
    ↓
V9
AI Financial Insights
    ↓
V10
Natural Language Analytics
```

The V1 design should remain simple enough to support this evolution without prematurely introducing unnecessary infrastructure.
