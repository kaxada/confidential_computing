from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.security import create_token
from app.core.db import get_session
from app.models import Role, User
from app.schemas import AccessChangeRequest, LoginRequest, SignupRequest
from app.services.log import log_event
from app.services.user import (
    create_user,
    delete_user_and_threads,
    get_user_by_email,
    request_access_change,
    verify_credentials,
)
from app.core.config import get_access_payload
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
    new_user = create_user(
        session,
        email=payload.email,
        password=payload.password,
        requested_role=role,
        first_name=payload.first_name,
        last_name=payload.last_name,
    )
    log_event(session, new_user.id, "signup", {"requested_role": requested_role})
    return {"status": "pending"}


@router.post("/login")
def login(payload: LoginRequest, session: Session = Depends(get_session)):
    user = verify_credentials(session, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.approved:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account pending approval")
    
    log_event(session, user.id, "login")
    
    effective_role_value = user.effective_role.value

    token = create_token(
        {
            "sub": str(user.id),
            "role": effective_role_value,
        }
    )
    return {"token": token, "role": effective_role_value}


@router.get("/me")
def me(user: User = Depends(require_approved)):
    access_payload = get_access_payload(user.effective_role)
    # Override privacy level in the payload if a temporary one is active
    current_privacy = user.effective_privacy_level
    if current_privacy != access_payload.get("privacy_level"):
        # We need to fetch the label for this privacy level
        from app.core.config import PRIVACY_METADATA
        p_meta = PRIVACY_METADATA.get(current_privacy, {})
        access_payload["privacy_level"] = current_privacy
        access_payload["privacy_label"] = p_meta.get("label", current_privacy)

    expires_at = user.role_expires_at
    if expires_at and expires_at.tzinfo is None:
        from datetime import timezone
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    return {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "requested_role": user.requested_role.value,
        "role": user.effective_role.value,
        "role_expires_at": expires_at,
        "temporary_privacy_level": user.temporary_privacy_level,
        "approved": bool(user.approved),
        "created_at": user.created_at,
        **access_payload,
    }


@router.post("/request-access")
def request_access(
    payload: AccessChangeRequest,
    session: Session = Depends(get_session),
    user: User = Depends(require_approved),
):
    role_enum_val = None
    if payload.role:
        try:
            role_enum_val = Role.from_str(payload.role)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")

    request_access_change(session, user.id, role=role_enum_val, privacy_level=payload.privacy_level, reason=payload.reason)
    
    log_data = {"reason": payload.reason}
    if role_enum_val:
        log_data["requested_role"] = role_enum_val.value
    if payload.privacy_level:
        log_data["requested_privacy_level"] = payload.privacy_level
        
    log_event(session, user.id, "access_request", log_data)
    return {"status": "requested"}


@router.post("/logout")
def logout(session: Session = Depends(get_session), user: User = Depends(require_approved)):
    log_event(session, user.id, "logout")
    return {"status": "logged_out"}


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(session: Session = Depends(get_session), user: User = Depends(require_approved)):
    if user.role == Role.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins cannot delete their account")

    deleted = delete_user_and_threads(session, user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
