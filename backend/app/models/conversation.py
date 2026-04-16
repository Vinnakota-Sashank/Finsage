"""
Conversation & Message models — AI chat history persistence.
"""

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class Conversation(SQLModel, table=True):
    __tablename__ = "conversations"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, foreign_key="users.id")
    title: Optional[str] = Field(default=None, max_length=200)  # auto-generated from first message
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class MessageBase(SQLModel):
    role: str = Field(max_length=10)  # user, assistant
    content: str
    chart_type: Optional[str] = Field(default=None, max_length=20)  # donut, bar, line, area, gauge, histogram
    chart_data_json: Optional[str] = None  # JSON string of chart data
    suggestions_json: Optional[str] = None  # JSON string of suggestion chips


class Message(MessageBase, table=True):
    __tablename__ = "messages"

    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: int = Field(index=True, foreign_key="conversations.id")
    tool_calls_json: Optional[str] = None  # JSON string of tool calls made
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MessageCreate(SQLModel):
    content: str


class MessageRead(MessageBase):
    id: int
    conversation_id: int
    created_at: datetime
