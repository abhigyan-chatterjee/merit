import re

from pydantic import BaseModel, Field, field_validator

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


class RegisterRequest(BaseModel):
    email: str = Field(..., description="Valid email address")
    display_name: str = Field(..., min_length=2, max_length=50, description="Display name")
    password: str = Field(..., min_length=10, description="Password (at least 10 characters)")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        clean = v.strip().lower()
        if not EMAIL_REGEX.match(clean):
            raise ValueError("Invalid email address format")
        return clean


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class UserResponse(BaseModel):
    id: str
    email: str
    display_name: str
    role: str
    created_at: str
    last_login_at: str | None = None

    model_config = {"from_attributes": True}


class AuthMessageResponse(BaseModel):
    message: str
