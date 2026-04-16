# Models package init — import all models here so SQLModel picks them up
from app.models.user import User, UserCreate, UserRead
from app.models.transaction import Transaction, TransactionCreate, TransactionRead
from app.models.goal import Goal, GoalCreate, GoalRead
from app.models.budget import Budget, BudgetCreate, BudgetRead
from app.models.alert import Alert, AlertCreate, AlertRead
from app.models.account import Account, AccountCreate, AccountRead
from app.models.conversation import Conversation, Message, MessageCreate, MessageRead

__all__ = [
    "User", "UserCreate", "UserRead",
    "Transaction", "TransactionCreate", "TransactionRead",
    "Goal", "GoalCreate", "GoalRead",
    "Budget", "BudgetCreate", "BudgetRead",
    "Alert", "AlertCreate", "AlertRead",
    "Account", "AccountCreate", "AccountRead",
    "Conversation", "Message", "MessageCreate", "MessageRead",
]
