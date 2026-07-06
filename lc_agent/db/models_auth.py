import uuid
from datetime import datetime, timezone

from sqlmodel import SQLModel, Field


def utcnow():
    return datetime.now(timezone.utc)


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    username: str = Field(index=True, unique=True)
    password_hash: str
    role: str = "user"  # "admin" or "user"
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class UserAgentAccess(SQLModel, table=True):
    __tablename__ = "user_agent_access"

    user_id: str = Field(primary_key=True)
    agent_id: str = Field(primary_key=True)
