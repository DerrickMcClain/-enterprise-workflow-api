import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    is_active: bool
    is_email_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=200)


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
