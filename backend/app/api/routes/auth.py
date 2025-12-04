from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.security import create_token
from app.core.db import get_session
from app.models import Role, User
from app.schemas import LoginRequest, SignupRequest
from app.services.user import (
    create_user,
    delete_user_and_threads,
    get_user_by_email,
    verify_credentials,
)
from app.api.deps.auth import require_approved

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, session: Session = Depends(get_session)):
    requested_role = payload.requested_role or Role.RESEARCHER.value
    try:
        role = Role.from_str(requested_role)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")
    if get_user_by_email(session, payload.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    create_user(session, email=payload.email, password=payload.password, requested_role=role)
    return {"status": "pending"}


@router.post("/login")
def login(payload: LoginRequest, session: Session = Depends(get_session)):
    user = verify_credentials(session, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.approved:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account pending approval")
    token = create_token(
        {
            "sub": str(user.id),
            "role": user.role.value if user.role else user.requested_role.value,
        }
    )
    return {"token": token, "role": user.role.value if user.role else None}


@router.get("/me")
def me(user: User = Depends(require_approved)):
    return {
        "id": user.id,
        "email": user.email,
        "requested_role": user.requested_role.value,
        "role": user.role.value if user.role else None,
        "approved": bool(user.approved),
        "created_at": user.created_at,
    }


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(session: Session = Depends(get_session), user: User = Depends(require_approved)):
    deleted = delete_user_and_threads(session, user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
