from datetime import datetime
from typing import List, Optional

from passlib.context import CryptContext
from sqlalchemy import select, or_
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


def list_all_pending_requests(session: Session) -> List[User]:
    """List new signups and existing users with pending role/privacy requests."""
    stmt = select(User).where(
        or_(
            User.approved == 0,
            User.requested_role != User.role,
            User.requested_privacy_level != None
        )
    )
    return list(session.execute(stmt).scalars().all())


def reject_access_request(session: Session, user_id: int) -> Optional[User]:
    """Reject pending requests for an existing user by resetting requested fields."""
    user = session.get(User, user_id)
    if not user:
        return None
    
    if user.approved:
        # Reset requested values to current actual values
        user.requested_role = user.role
        user.requested_privacy_level = None
        user.request_reason = None
        session.add(user)
        session.commit()
        session.refresh(user)
    else:
        # For unapproved users, rejection usually means deletion, 
        # but let's leave that to delete_pending_user. 
        # This function is primarily for access requests.
        pass

    return user


def list_all_users(session: Session) -> List[User]:
    return list(session.execute(select(User)).scalars().all())


from app.core.config import ROLE_METADATA

def approve_user_access(
    session: Session, 
    user_id: int, 
    role: Optional[Role] = None, 
    privacy_level: Optional[str] = None,
    expires_at: Optional[datetime] = None
) -> Optional[User]:
    user = session.get(User, user_id)
    if not user:
        return None
    
    if not user.approved:
        # First approval: Always requires a permanent role
        if not role:
             # If no role provided, stick to requested or fallback?
             role = user.requested_role
        
        user.role = role
        user.temporary_role = None
        user.temporary_privacy_level = None
        user.role_expires_at = None
        user.approved = 1
        user.requested_role = role
        user.requested_privacy_level = None
    else:
        # Already approved
        if expires_at:
            # Temporary Access Grant
            if privacy_level:
                # Grant temporary privacy level
                user.temporary_privacy_level = privacy_level
                user.role_expires_at = expires_at
                # Do NOT change user.role
            elif role:
                # Fallback: if ONLY role is passed with expiration, map to privacy
                role_str = role.value
                target_privacy = ROLE_METADATA.get(role_str, {}).get("privacy_level", "moderate")
                user.temporary_privacy_level = target_privacy
                user.role_expires_at = expires_at
            
            # Clear request flags so it drops off the pending list
            user.requested_privacy_level = None
            user.request_reason = None
            # If they requested a role change but got a temporary privacy change, 
            # we should probably leave requested_role alone? 
            # Or if this WAS the response to that request, clear it?
            # Let's assume clear it to be safe, or set it back to current role.
            user.requested_role = user.role
        else:
            # Permanent update
            if role:
                user.role = role
                user.requested_role = role
            
            # Reset temporary stuff
            user.temporary_role = None
            user.temporary_privacy_level = None
            user.role_expires_at = None
            user.requested_privacy_level = None

    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def request_access_change(
    session: Session, 
    user_id: int, 
    role: Optional[Role] = None, 
    privacy_level: Optional[str] = None, 
    reason: str = None
) -> Optional[User]:
    user = session.get(User, user_id)
    if not user:
        return None
    
    if role:
        user.requested_role = role
    
    if privacy_level:
        user.requested_privacy_level = privacy_level
    
    user.request_reason = reason
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
