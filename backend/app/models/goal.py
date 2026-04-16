"""
Goal model — user financial goals (savings targets).
"""

from datetime import datetime, date
from typing import Optional
from sqlmodel import SQLModel, Field


class GoalBase(SQLModel):
    name: str = Field(max_length=100)  # "Goa Trip", "Emergency Fund"
    target_amount: float
    current_amount: float = 0.0
    deadline: date
    priority: str = Field(default="medium", max_length=10)  # low, medium, high
    monthly_contribution: Optional[float] = None


class Goal(GoalBase, table=True):
    __tablename__ = "goals"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, foreign_key="users.id")
    status: str = Field(default="active", max_length=15)  # active, completed, paused, failed
    probability: Optional[float] = None  # computed: 0.0–1.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class GoalCreate(GoalBase):
    pass


class GoalRead(GoalBase):
    id: int
    user_id: int
    status: str
    probability: Optional[float] = None
    created_at: datetime
