from dataclasses import dataclass
from datetime import datetime, timezone
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
    INTERN = "intern"
    AUDITOR = "auditor"
    CLINICIAN = "clinician"
    ANALYST = "analyst"

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
    role_expires_at: Optional[datetime] = None


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    requested_role = Column(role_enum(), nullable=False, default=Role.RESEARCHER)
    requested_privacy_level = Column(String(50), nullable=True)
    role = Column(role_enum(), nullable=True)
    temporary_role = Column(role_enum(), nullable=True)
    temporary_privacy_level = Column(String(50), nullable=True)
    role_expires_at = Column(DateTime(timezone=True), nullable=True)
    request_reason = Column(Text, nullable=True)
    approved = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    threads = relationship("ChatThread", back_populates="user")
    logs = relationship("UserLog", back_populates="user", cascade="all, delete-orphan")

    @property
    def effective_role(self) -> Role:
        """Return the current active role (identity)."""
        return self.role or self.requested_role

    @property
    def effective_privacy_level(self) -> str:
        """Return the active privacy level, checking temporary overrides."""
        # Avoid circular imports by importing here or assuming config availability
        from app.core.config import ROLE_METADATA, settings

        # Check temporary override
        if self.temporary_privacy_level and self.role_expires_at:
            now = datetime.now(timezone.utc)
            expires_at = self.role_expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            
            if now < expires_at:
                return self.temporary_privacy_level

        # Fallback to role-based privacy
        role_val = self.effective_role.value
        role_meta = ROLE_METADATA.get(role_val)
        return (role_meta or {}).get("privacy_level") or settings.default_privacy_level


class UserLog(Base):
    __tablename__ = "user_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    event = Column(String(50), nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="logs")


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
