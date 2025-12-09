from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.db import get_session
from app.core.security import decode_token
from app.models import Role, User

security = HTTPBearer()


def get_current_user(session: Session = Depends(get_session), creds: HTTPAuthorizationCredentials = Depends(security)) -> User:
    payload = decode_token(creds.credentials)
    user_id = int(payload.get("sub"))
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_role(role: Role):
    def _checker(user: User = Depends(get_current_user)) -> User:
        if user.effective_role != role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return user

    return _checker


def require_approved(user: User = Depends(get_current_user)) -> User:
    if not user.approved:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not approved")
    return user
