from typing import Any

from pydantic import BaseModel, EmailStr, Field, field_validator


class ChatRequest(BaseModel):
    business: str = Field(default="LeadHunter")
    message: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    reply: str
    business: str
    status: str = "ok"
    leads: list[dict[str, Any]] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class HashRequest(BaseModel):
    text: str = Field(..., min_length=1)


class HashResponse(BaseModel):
    algorithm: str
    digest: str
    input_length: int
    note: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=255)
    organization_name: str = Field(..., min_length=1, max_length=255)
    remember_me: bool = False

    @field_validator("password")
    @classmethod
    def validate_password_bytes(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("La contraseña no puede superar 72 bytes en UTF-8.")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)
    remember_me: bool = False

    @field_validator("password")
    @classmethod
    def validate_password_bytes(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("La contraseña no puede superar 72 bytes en UTF-8.")
        return value
