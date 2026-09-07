from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

Amount = Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2)]


def _parse_month(value: date | str) -> date:
    if isinstance(value, date):
        return date(value.year, value.month, 1)
    try:
        parsed = datetime.strptime(value, "%Y-%m").date()
    except ValueError as exc:
        raise ValueError("month must be in YYYY-MM format") from exc
    return date(parsed.year, parsed.month, 1)


class BudgetCreate(BaseModel):
    category_id: int
    amount: Amount
    month: date

    @field_validator("month", mode="before")
    @classmethod
    def parse_month(cls, value: date | str) -> date:
        return _parse_month(value)


class BudgetUpdate(BaseModel):
    category_id: int
    amount: Amount
    month: date

    @field_validator("month", mode="before")
    @classmethod
    def parse_month(cls, value: date | str) -> date:
        return _parse_month(value)


class BudgetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    category_id: int
    amount: Decimal
    month: date
    created_at: datetime
    updated_at: datetime

    @field_serializer("month")
    def serialize_month(self, value: date) -> str:
        return value.strftime("%Y-%m")
