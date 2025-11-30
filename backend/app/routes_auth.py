from fastapi import APIRouter, HTTPException, status

from .auth import create_token
from .models import Role
from .store import store

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(email: str, password: str, requested_role: Role = Role.RESEARCHER):
    if store.get_by_email(email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    store.create_user(email=email, password=password, requested_role=requested_role)
    return {"status": "pending"}


@router.post("/login")
def login(email: str, password: str):
    user = store.verify_credentials(email, password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.approved:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account pending approval")
    token = create_token(user)
    return {"token": token, "role": user.role.value if user.role else None}
