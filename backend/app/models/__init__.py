from dataclasses import dataclass
from enum import Enum
from typing import Optional

from sqlalchemy import Column, DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.core.db import Base


class Role(str, Enum):
    ADMIN = "admin"
    RESEARCHER = "researcher"
    STUDENT = "student"
    PI = "pi"

    @classmethod
    def from_str(cls, value: str) -> "Role":
        """Parse a role string case-insensitively."""
        if value is None:
            raise ValueError("Role value is required")
        return cls(value.strip().lower())


def role_enum():
    """Shared SQLAlchemy Enum config that stores the string values."""
    return SAEnum(Role, name="role", values_callable=lambda enum: [e.value for e in enum])


@dataclass
class UserDTO:
    id: int
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    requested_role: Role
    role: Optional[Role]
    approved: bool


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    requested_role = Column(role_enum(), nullable=False, default=Role.RESEARCHER)
    role = Column(role_enum(), nullable=True)
    approved = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    threads = relationship("ChatThread", back_populates="user")


class ChatThread(Base):
    __tablename__ = "chat_threads"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="threads")
    messages = relationship("ChatMessage", back_populates="thread", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True)
    thread_id = Column(Integer, ForeignKey("chat_threads.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String(32), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    thread = relationship("ChatThread", back_populates="messages")
