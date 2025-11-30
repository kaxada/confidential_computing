from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .config import settings
from .db import get_session
from .models import Role, User

security = HTTPBearer()


def create_token(user: User) -> str:
    now = datetime.utcnow()
    payload = {
        "sub": str(user.id),
        "role": user.role.value if user.role else user.requested_role.value,  # default to requested if not assigned yet
        "exp": now + timedelta(minutes=settings.jwt_exp_minutes),
        "iat": now,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def get_current_user(session: Session = Depends(get_session), creds: HTTPAuthorizationCredentials = Depends(security)) -> User:
    payload = decode_token(creds.credentials)
    user_id = int(payload.get("sub"))
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_role(role: Role):
    def _checker(user: User = Depends(get_current_user)) -> User:
        if user.role != role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return user

    return _checker


def require_approved(user: User = Depends(get_current_user)) -> User:
    if not user.approved:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not approved")
    return user
