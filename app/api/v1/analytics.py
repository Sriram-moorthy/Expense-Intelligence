from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.exceptions import INVALID_ANALYTICS_QUERY, AppError
from app.db.session import get_db
from app.models.user import User
from app.schemas.analytics import (
    AnalyticsSummaryResponse,
    BudgetAnalyticsResponse,
    CategoryAnalyticsResponse,
    TrendsResponse,
    parse_month,
)
from app.services.analytics import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])

PeriodQuery = Literal["this_month", "last_month"]
GroupByQuery = Literal["day", "month"]


@router.get("/summary", response_model=AnalyticsSummaryResponse)
def get_summary(
    period: PeriodQuery | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalyticsSummaryResponse:
    return AnalyticsService(db).get_summary(
        current_user.id, period, start_date, end_date
    )


@router.get("/categories", response_model=CategoryAnalyticsResponse)
def get_category_analytics(
    period: PeriodQuery | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CategoryAnalyticsResponse:
    return AnalyticsService(db).get_category_analytics(
        current_user.id, period, start_date, end_date
    )


@router.get("/trends", response_model=TrendsResponse)
def get_trends(
    group_by: GroupByQuery,
    period: PeriodQuery | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TrendsResponse:
    return AnalyticsService(db).get_trends(
        current_user.id, group_by, period, start_date, end_date
    )


@router.get("/budgets", response_model=BudgetAnalyticsResponse)
def get_budget_analytics(
    month: str = Query(..., description="Budget month in YYYY-MM format"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BudgetAnalyticsResponse:
    try:
        month_date = parse_month(month)
    except ValueError:
        raise AppError(422, INVALID_ANALYTICS_QUERY, "month must be in YYYY-MM format")
    return AnalyticsService(db).get_budget_analytics(current_user.id, month_date)
