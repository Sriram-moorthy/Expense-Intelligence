from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.category import CategoryType

Amount = Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2)]


class TransactionCreate(BaseModel):
    amount: Amount
    type: CategoryType
    category_id: int
    description: str | None = Field(default=None, max_length=255)
    transaction_date: date

    @field_validator("description")
    @classmethod
    def strip_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class TransactionUpdate(BaseModel):
    amount: Amount
    type: CategoryType
    category_id: int
    description: str | None = Field(default=None, max_length=255)
    transaction_date: date

    @field_validator("description")
    @classmethod
    def strip_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    category_id: int
    amount: Decimal
    type: str
    description: str | None
    transaction_date: date
    created_at: datetime
    updated_at: datetime
