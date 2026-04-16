"""
Alert model — proactive intelligence notifications.
"""

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class AlertBase(SQLModel):
    severity: str = Field(max_length=10)  # critical, warning, info, insight
    alert_type: str = Field(max_length=30)  # spending_spike, budget_breach, goal_risk, recurring_anomaly, credit_health
    title: str = Field(max_length=200)
    description: str
    recommendation: Optional[str] = None


class Alert(AlertBase, table=True):
    __tablename__ = "alerts"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, foreign_key="users.id")
    is_read: bool = Field(default=False)
    action_url: Optional[str] = Field(default=None, max_length=255)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AlertCreate(AlertBase):
    pass


class AlertRead(AlertBase):
    id: int
    user_id: int
    is_read: bool
    created_at: datetime
