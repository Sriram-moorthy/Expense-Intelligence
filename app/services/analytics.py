from calendar import monthrange
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import INVALID_ANALYTICS_QUERY, INVALID_DATE_RANGE, AppError
from app.repositories.analytics import AnalyticsRepository
from app.schemas.analytics import (
    AnalyticsSummaryResponse,
    BudgetAnalyticsItem,
    BudgetAnalyticsResponse,
    CategoryAnalyticsItem,
    CategoryAnalyticsResponse,
    TrendPoint,
    TrendsResponse,
)

_ZERO = Decimal("0.00")
_HUNDRED = Decimal("100")
_NEAR_LIMIT = Decimal("80")
_QUANTIZE = Decimal("0.01")


class AnalyticsService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.analytics = AnalyticsRepository(db)

    def get_summary(
        self,
        user_id: int,
        period: str | None,
        start_date: date | None,
        end_date: date | None,
    ) -> AnalyticsSummaryResponse:
        start, end = self._resolve_range(period, start_date, end_date)
        income, expense, count = self.analytics.summarize_transactions(
            user_id, start, end
        )
        return AnalyticsSummaryResponse(
            total_income=income,
            total_expense=expense,
            balance=income - expense,
            transaction_count=count,
        )

    def get_category_analytics(
        self,
        user_id: int,
        period: str | None,
        start_date: date | None,
        end_date: date | None,
    ) -> CategoryAnalyticsResponse:
        start, end = self._resolve_range(period, start_date, end_date)
        rows = self.analytics.expense_totals_by_category(user_id, start, end)
        return CategoryAnalyticsResponse(
            categories=[
                CategoryAnalyticsItem(
                    category_id=category_id,
                    name=name,
                    total_expense=total,
                    transaction_count=count,
                )
                for category_id, name, total, count in rows
            ]
        )

    def get_trends(
        self,
        user_id: int,
        group_by: str,
        period: str | None,
        start_date: date | None,
        end_date: date | None,
    ) -> TrendsResponse:
        start, end = self._resolve_range(period, start_date, end_date)
        rows = self.analytics.trend_totals(user_id, group_by, start, end)
        points = [
            TrendPoint(
                period=self._format_period(bucket, group_by),
                total_income=income,
                total_expense=expense,
                balance=income - expense,
                transaction_count=count,
            )
            for bucket, income, expense, count in rows
        ]
        return TrendsResponse(group_by=group_by, points=points)

    def get_budget_analytics(
        self, user_id: int, month: date
    ) -> BudgetAnalyticsResponse:
        month_start = date(month.year, month.month, 1)
        month_end = date(
            month.year, month.month, monthrange(month.year, month.month)[1]
        )
        budgets = self.analytics.budgets_for_month(user_id, month_start)
        spent_rows = self.analytics.expense_totals_by_category(
            user_id, month_start, month_end
        )
        spent_by_category = {
            category_id: total for category_id, _name, total, _count in spent_rows
        }

        items: list[BudgetAnalyticsItem] = []
        for budget, name in budgets:
            spent = spent_by_category.get(budget.category_id, _ZERO)
            remaining = budget.amount - spent
            percentage = (spent / budget.amount * _HUNDRED).quantize(
                _QUANTIZE, rounding=ROUND_HALF_UP
            )
            if spent > budget.amount:
                status = "OVER_BUDGET"
            elif percentage >= _NEAR_LIMIT:
                status = "NEAR_LIMIT"
            else:
                status = "UNDER_BUDGET"
            items.append(
                BudgetAnalyticsItem(
                    category_id=budget.category_id,
                    name=name,
                    budget=budget.amount,
                    spent=spent,
                    remaining=remaining,
                    percentage_used=percentage,
                    status=status,
                )
            )
        return BudgetAnalyticsResponse(month=month_start, budgets=items)

    def _resolve_range(
        self,
        period: str | None,
        start_date: date | None,
        end_date: date | None,
    ) -> tuple[date | None, date | None]:
        has_custom = start_date is not None or end_date is not None
        if period is not None and has_custom:
            raise AppError(
                400,
                INVALID_ANALYTICS_QUERY,
                "Use either period or start_date and end_date, not both",
            )
        if (start_date is None) != (end_date is None):
            raise AppError(
                400,
                INVALID_ANALYTICS_QUERY,
                "start_date and end_date must both be provided",
            )
        if start_date is not None and end_date is not None:
            if start_date > end_date:
                raise AppError(
                    422,
                    INVALID_DATE_RANGE,
                    "start_date must be less than or equal to end_date",
                )
            return start_date, end_date
        if period == "this_month":
            return self._month_bounds(date.today())
        if period == "last_month":
            today = date.today()
            if today.month == 1:
                previous = date(today.year - 1, 12, 1)
            else:
                previous = date(today.year, today.month - 1, 1)
            return self._month_bounds(previous)
        return None, None

    def _month_bounds(self, month_date: date) -> tuple[date, date]:
        start = date(month_date.year, month_date.month, 1)
        end = date(
            month_date.year,
            month_date.month,
            monthrange(month_date.year, month_date.month)[1],
        )
        return start, end

    def _format_period(self, bucket: date, group_by: str) -> str:
        if group_by == "month":
            return bucket.strftime("%Y-%m")
        return bucket.isoformat()
