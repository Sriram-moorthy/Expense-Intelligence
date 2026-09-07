from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

CategoryType = Literal["INCOME", "EXPENSE"]


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    type: CategoryType

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("name cannot be empty")
        return stripped


class CategoryUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    type: CategoryType

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("name cannot be empty")
        return stripped


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    type: str
    created_at: datetime
    updated_at: datetime
