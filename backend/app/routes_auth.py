from fastapi import APIRouter, HTTPException, status

from .auth import create_token
from .models import Role
from .schemas import LoginRequest, SignupRequest
from .store import store

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest):
    requested_role = payload.requested_role or Role.RESEARCHER.value
    try:
        role = Role(requested_role)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")
    if store.get_by_email(payload.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    store.create_user(email=payload.email, password=payload.password, requested_role=role)
    return {"status": "pending"}


@router.post("/login")
def login(payload: LoginRequest):
    user = store.verify_credentials(payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.approved:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account pending approval")
    token = create_token(user)
    return {"token": token, "role": user.role.value if user.role else None}
