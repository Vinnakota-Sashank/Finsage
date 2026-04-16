"""
Budget model — per-category monthly spending limits.
"""

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class BudgetBase(SQLModel):
    category: str = Field(max_length=50, index=True)
    monthly_limit: float
    alert_threshold: float = 0.8  # alert at 80% usage


class Budget(BudgetBase, table=True):
    __tablename__ = "budgets"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class BudgetCreate(BudgetBase):
    pass


class BudgetRead(BudgetBase):
    id: int
    user_id: int
