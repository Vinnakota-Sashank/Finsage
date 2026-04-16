"""
Account model — linked bank accounts.
"""

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class AccountBase(SQLModel):
    bank_name: str = Field(max_length=100)
    account_type: str = Field(default="savings", max_length=20)  # savings, current, credit_card
    account_number_masked: Optional[str] = Field(default=None, max_length=20)  # XXXX1234
    balance: float = 0.0


class Account(AccountBase, table=True):
    __tablename__ = "accounts"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, foreign_key="users.id")
    aa_linked: bool = Field(default=False)  # linked via Account Aggregator?
    last_synced: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AccountCreate(AccountBase):
    pass


class AccountRead(AccountBase):
    id: int
    user_id: int
    aa_linked: bool
    last_synced: Optional[datetime] = None
