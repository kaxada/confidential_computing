from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import HTTPException, status

from .config import settings


def create_token(payload: dict, expires_minutes: Optional[int] = None) -> str:
    data = payload.copy()
    now = datetime.utcnow()
    exp_minutes = expires_minutes or settings.jwt_exp_minutes
    data.update({"iat": now, "exp": now + timedelta(minutes=exp_minutes)})
    return jwt.encode(data, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
