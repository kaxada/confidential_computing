from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .auth import create_token
from .db import get_session
from .models import Role
from .schemas import LoginRequest, SignupRequest
from .services import create_user, get_user_by_email, verify_credentials

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, session: Session = Depends(get_session)):
    requested_role = payload.requested_role or Role.RESEARCHER.value
    try:
        role = Role(requested_role)
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
    token = create_token(user)
    return {"token": token, "role": user.role.value if user.role else None}
