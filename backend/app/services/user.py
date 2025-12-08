from typing import List, Optional

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ChatThread, Role, User

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def init_admin(session: Session):
    admin_email = "admin@example.com"
    stmt = select(User).where(User.email == admin_email)
    if session.execute(stmt).scalar_one_or_none() is None:
        admin = User(
            email=admin_email,
            password_hash=hash_password("admin"),
            requested_role=Role.ADMIN,
            role=Role.ADMIN,
            approved=1,
        )
        session.add(admin)
        session.commit()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_user(
    session: Session,
    email: str,
    password: str,
    requested_role: Role,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
) -> User:
    user = User(
        email=email.lower(),
        password_hash=hash_password(password),
        first_name=first_name,
        last_name=last_name,
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


def delete_pending_user(session: Session, user_id: int) -> bool:
    """Delete a user that has not been approved yet."""
    user = session.get(User, user_id)
    if not user:
        return False
    if user.approved:
        return False
    session.delete(user)
    session.commit()
    return True


def delete_user_and_threads(session: Session, user_id: int) -> bool:
    """Delete a user and their chat data."""
    user = session.get(User, user_id)
    if not user:
        return False
    threads = session.query(ChatThread).filter_by(user_id=user_id).all()
    for t in threads:
        session.delete(t)  # cascades to messages
    session.delete(user)
    session.commit()
    return True
