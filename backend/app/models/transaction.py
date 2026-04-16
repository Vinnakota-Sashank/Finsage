"""
Transaction model — the core financial data entity.
Every bank transaction, UPI payment, SIP debit, and manual entry lives here.
"""

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class TransactionBase(SQLModel):
    amount: float
    category: str = Field(max_length=50, index=True)  # food, rent, transport, shopping, etc.
    subcategory: Optional[str] = Field(default=None, max_length=50)  # swiggy, zomato, uber, etc.
    merchant: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = Field(default=None, max_length=255)
    payment_mode: Optional[str] = Field(default=None, max_length=30)  # upi, credit_card, neft, auto_debit
    transaction_type: str = Field(default="debit", max_length=10)  # debit, credit
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    is_recurring: bool = Field(default=False)


class Transaction(TransactionBase, table=True):
    __tablename__ = "transactions"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, foreign_key="users.id")
    source: str = Field(default="manual", max_length=20)  # manual, aa, sms, csv
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TransactionCreate(TransactionBase):
    pass


class TransactionRead(TransactionBase):
    id: int
    user_id: int
    source: str
    created_at: datetime
