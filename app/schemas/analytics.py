from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, field_serializer, field_validator

Period = Literal["this_month", "last_month"]
GroupBy = Literal["day", "month"]
BudgetStatus = Literal["UNDER_BUDGET", "NEAR_LIMIT", "OVER_BUDGET"]


def parse_month(value: date | str) -> date:
    if isinstance(value, date):
        return date(value.year, value.month, 1)
    try:
        parsed = datetime.strptime(value, "%Y-%m").date()
    except ValueError as exc:
        raise ValueError("month must be in YYYY-MM format") from exc
    return date(parsed.year, parsed.month, 1)


class AnalyticsSummaryResponse(BaseModel):
    total_income: Decimal
    total_expense: Decimal
    balance: Decimal
    transaction_count: int


class CategoryAnalyticsItem(BaseModel):
    category_id: int
    name: str
    total_expense: Decimal
    transaction_count: int


class CategoryAnalyticsResponse(BaseModel):
    categories: list[CategoryAnalyticsItem]


class TrendPoint(BaseModel):
    period: str
    total_income: Decimal
    total_expense: Decimal
    balance: Decimal
    transaction_count: int


class TrendsResponse(BaseModel):
    group_by: GroupBy
    points: list[TrendPoint]


class BudgetAnalyticsItem(BaseModel):
    category_id: int
    name: str
    budget: Decimal
    spent: Decimal
    remaining: Decimal
    percentage_used: Decimal
    status: BudgetStatus


class BudgetAnalyticsResponse(BaseModel):
    month: date
    budgets: list[BudgetAnalyticsItem]

    @field_validator("month", mode="before")
    @classmethod
    def parse_month_value(cls, value: date | str) -> date:
        return parse_month(value)

    @field_serializer("month")
    def serialize_month(self, value: date) -> str:
        return value.strftime("%Y-%m")
