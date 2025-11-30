from typing import List, Optional, Tuple

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import ChatMessage, ChatThread, Role, User

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def init_admin(session: Session):
    admin_email = "admin@example.com"
    stmt = select(User).where(User.email == admin_email)
    if session.execute(stmt).scalar_one_or_none() is None:
        admin = User(
            email=admin_email,
            password_hash=pwd_context.hash("admin"),
            requested_role=Role.ADMIN,
            role=Role.ADMIN,
            approved=1,
        )
        session.add(admin)
        session.commit()


def create_user(session: Session, email: str, password: str, requested_role: Role) -> User:
    user = User(
        email=email.lower(),
        password_hash=pwd_context.hash(password),
        requested_role=requested_role,
        role=None,
        approved=0,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def get_user_by_email(session: Session, email: str) -> Optional[User]:
    stmt = select(User).where(User.email == email.lower())
    return session.execute(stmt).scalar_one_or_none()


def verify_credentials(session: Session, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(session, email)
    if not user:
        return None
    if not pwd_context.verify(password, user.password_hash):
        return None
    return user


def list_pending_users(session: Session) -> List[User]:
    stmt = select(User).where(User.approved == 0)
    return list(session.execute(stmt).scalars().all())


def approve_user(session: Session, user_id: int, role: Role) -> Optional[User]:
    user = session.get(User, user_id)
    if not user:
        return None
    user.role = role
    user.approved = 1
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def get_or_create_thread(session: Session, user_id: int, thread_id: Optional[int] = None, title: Optional[str] = None) -> ChatThread:
    if thread_id:
        thread = session.get(ChatThread, thread_id)
        if thread and thread.user_id == user_id:
            return thread
    thread = ChatThread(user_id=user_id, title=title)
    session.add(thread)
    session.commit()
    session.refresh(thread)
    return thread


def add_message(session: Session, thread: ChatThread, user_id: int, role: str, content: str) -> ChatMessage:
    msg = ChatMessage(thread_id=thread.id, user_id=user_id, role=role, content=content)
    session.add(msg)
    session.commit()
    session.refresh(msg)
    return msg


def list_threads(session: Session, user_id: int) -> List[ChatThread]:
    stmt = select(ChatThread).where(ChatThread.user_id == user_id).order_by(ChatThread.created_at.desc())
    return list(session.execute(stmt).scalars().all())


def list_messages(session: Session, user_id: int, thread_id: int) -> List[ChatMessage]:
    stmt = select(ChatMessage).where(ChatMessage.user_id == user_id, ChatMessage.thread_id == thread_id).order_by(ChatMessage.created_at)
    return list(session.execute(stmt).scalars().all())
