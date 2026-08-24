from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    username: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(min_length=1, max_length=255)

    @field_validator("username")
    @classmethod
    def strip_username(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("username cannot be empty")
        return stripped


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=255)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    created_at: datetime
    updated_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
