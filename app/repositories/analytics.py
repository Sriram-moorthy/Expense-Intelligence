from datetime import date
from decimal import Decimal

from sqlalchemy import Date, case, cast, func, literal, select
from sqlalchemy.orm import Session

from app.models.budget import Budget
from app.models.category import Category
from app.models.transaction import Transaction

_ZERO = literal(Decimal("0.00"))


class AnalyticsRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def summarize_transactions(
        self, user_id: int, start_date: date | None, end_date: date | None
    ) -> tuple[Decimal, Decimal, int]:
        income = func.coalesce(
            func.sum(
                case(
                    (Transaction.type == "INCOME", Transaction.amount),
                    else_=_ZERO,
                )
            ),
            _ZERO,
        )
        expense = func.coalesce(
            func.sum(
                case(
                    (Transaction.type == "EXPENSE", Transaction.amount),
                    else_=_ZERO,
                )
            ),
            _ZERO,
        )
        stmt = select(income, expense, func.count(Transaction.id)).where(
            Transaction.user_id == user_id,
            *self._date_filters(start_date, end_date),
        )
        row = self.db.execute(stmt).one()
        return (
            Decimal(str(row[0])),
            Decimal(str(row[1])),
            int(row[2]),
        )

    def expense_totals_by_category(
        self, user_id: int, start_date: date | None, end_date: date | None
    ) -> list[tuple[int, str, Decimal, int]]:
        total = func.coalesce(func.sum(Transaction.amount), _ZERO)
        stmt = (
            select(
                Category.id,
                Category.name,
                total,
                func.count(Transaction.id),
            )
            .join(Category, Category.id == Transaction.category_id)
            .where(
                Transaction.user_id == user_id,
                Transaction.type == "EXPENSE",
                *self._date_filters(start_date, end_date),
            )
            .group_by(Category.id, Category.name)
            .order_by(Category.id)
        )
        rows = self.db.execute(stmt).all()
        return [
            (int(row[0]), str(row[1]), Decimal(str(row[2])), int(row[3]))
            for row in rows
        ]

    def trend_totals(
        self,
        user_id: int,
        group_by: str,
        start_date: date | None,
        end_date: date | None,
    ) -> list[tuple[date, Decimal, Decimal, int]]:
        if group_by == "month":
            bucket = cast(
                func.date_trunc("month", Transaction.transaction_date),
                Date,
            )
        else:
            bucket = Transaction.transaction_date

        income = func.coalesce(
            func.sum(
                case(
                    (Transaction.type == "INCOME", Transaction.amount),
                    else_=_ZERO,
                )
            ),
            _ZERO,
        )
        expense = func.coalesce(
            func.sum(
                case(
                    (Transaction.type == "EXPENSE", Transaction.amount),
                    else_=_ZERO,
                )
            ),
            _ZERO,
        )
        stmt = (
            select(bucket, income, expense, func.count(Transaction.id))
            .where(
                Transaction.user_id == user_id,
                *self._date_filters(start_date, end_date),
            )
            .group_by(bucket)
            .order_by(bucket)
        )
        rows = self.db.execute(stmt).all()
        return [
            (row[0], Decimal(str(row[1])), Decimal(str(row[2])), int(row[3]))
            for row in rows
        ]

    def budgets_for_month(
        self, user_id: int, month: date
    ) -> list[tuple[Budget, str]]:
        stmt = (
            select(Budget, Category.name)
            .join(Category, Category.id == Budget.category_id)
            .where(Budget.user_id == user_id, Budget.month == month)
            .order_by(Budget.id)
        )
        return [(row[0], str(row[1])) for row in self.db.execute(stmt).all()]

    def _date_filters(self, start_date: date | None, end_date: date | None):
        filters = []
        if start_date is not None:
            filters.append(Transaction.transaction_date >= start_date)
        if end_date is not None:
            filters.append(Transaction.transaction_date <= end_date)
        return filters
