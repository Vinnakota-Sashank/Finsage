"""
User model — core identity for FinSage users.
"""

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class UserBase(SQLModel):
    name: str = Field(max_length=100)
    email: str = Field(max_length=255, unique=True, index=True)
    phone: Optional[str] = Field(default=None, max_length=15)
    city: Optional[str] = Field(default=None, max_length=100)
    occupation: Optional[str] = Field(default=None, max_length=100)
    monthly_income: Optional[float] = None
    tax_bracket: Optional[float] = None  # e.g., 0.30 for 30%
    risk_appetite: Optional[str] = Field(default="moderate", max_length=20)  # conservative, moderate, aggressive


class User(UserBase, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: Optional[str] = Field(default=None, max_length=255)
    auth_provider: str = Field(default="local", max_length=20)  # local, google
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserCreate(SQLModel):
    name: str
    email: str
    password: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    occupation: Optional[str] = None
    monthly_income: Optional[float] = None


class UserRead(SQLModel):
    id: int
    name: str
    email: str
    phone: Optional[str] = None
    city: Optional[str] = None
    occupation: Optional[str] = None
    monthly_income: Optional[float] = None
    tax_bracket: Optional[float] = None
    risk_appetite: Optional[str] = None
    created_at: datetime
