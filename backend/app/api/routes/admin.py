from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps.auth import require_role
from app.core.db import get_session
from app.models import Role, User, UserLog
from app.schemas import AdminAccessUpdateRequest, ApproveRequest
from app.services.log import log_event
from app.services.user import (
    approve_user_access,
    delete_pending_user,
    delete_user_and_threads,
    list_all_users,
    list_pending_users,
    list_all_pending_requests,
    reject_access_request,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users")
def get_all_users(session: Session = Depends(get_session), user: User = Depends(require_role(Role.ADMIN))):
    users = list_all_users(session)
    
    def ensure_utc(dt):
        if dt and dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    return [
        {
            "id": u.id,
            "email": u.email,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "role": u.role.value if u.role else None,
            "base_role": u.role.value if u.role else None,
            "requested_role": u.requested_role.value,
            "role_expires_at": ensure_utc(u.role_expires_at),
            "request_reason": u.request_reason,
            "approved": u.approved,
        }
        for u in users
    ]


@router.get("/logs")
def get_logs(session: Session = Depends(get_session), user: User = Depends(require_role(Role.ADMIN))):
    stmt = select(UserLog).order_by(UserLog.created_at.desc()).limit(100)
    logs = session.execute(stmt).scalars().all()
    
    def ensure_utc(dt):
        if dt and dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    return [
        {
            "id": l.id,
            "user_id": l.user_id,
            "event": l.event,
            "details": l.details,
            "request_metadata": l.request_metadata,
            "created_at": ensure_utc(l.created_at),
        }
        for l in logs
    ]


@router.put("/users/{user_id}/access")
def update_user_access(
    user_id: int,
    payload: AdminAccessUpdateRequest,
    session: Session = Depends(get_session),
    admin: User = Depends(require_role(Role.ADMIN)),
):
    role_enum_val = None
    if payload.role:
        try:
            role_enum_val = Role.from_str(payload.role)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")
    
    expires_at = payload.expires_at
    if payload.duration_minutes is not None:
        if not (0.25 <= payload.duration_minutes <= 60):
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Duration must be between 0.25 and 60 minutes")
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=payload.duration_minutes)

    updated = approve_user_access(session, user_id, role=role_enum_val, privacy_level=payload.privacy_level, expires_at=expires_at)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    log_data = {
        "target_user_id": user_id, 
        "duration": payload.duration_minutes,
        "expires_at": str(expires_at) if expires_at else None
    }
    if role_enum_val:
        log_data["new_role"] = role_enum_val.value
    if payload.privacy_level:
        log_data["new_privacy_level"] = payload.privacy_level
        
    log_event(session, admin.id, "admin_update_access", log_data)
    
    expires_at_response = updated.role_expires_at
    if expires_at_response and expires_at_response.tzinfo is None:
        expires_at_response = expires_at_response.replace(tzinfo=timezone.utc)

    return {
        "status": "updated", 
        "role": updated.role.value if updated.role else None, 
        "temporary_privacy_level": updated.temporary_privacy_level,
        "expires_at": expires_at_response
    }


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    session: Session = Depends(get_session),
    admin: User = Depends(require_role(Role.ADMIN)),
):
    deleted = delete_user_and_threads(session, user_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    log_event(session, admin.id, "admin_delete_user", {"target_user_id": user_id})
    return {"status": "deleted"}


@router.get("/pending")
def list_pending(session: Session = Depends(get_session), user: User = Depends(require_role(Role.ADMIN))):
    pending = list_all_pending_requests(session)
    return [
        {
            "id": u.id, 
            "email": u.email, 
            "requested_role": u.requested_role.value if u.requested_role else None,
            "role": u.role.value if u.role else None,
            "requested_privacy_level": u.requested_privacy_level,
            "request_reason": u.request_reason,
            "approved": u.approved
        }
        for u in pending
    ]


@router.post("/requests/{user_id}/reject")
def reject_request(user_id: int, session: Session = Depends(get_session), admin: User = Depends(require_role(Role.ADMIN))):
    rejected = reject_access_request(session, user_id)
    if not rejected:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    log_event(session, admin.id, "admin_reject_request", {"target_user_id": user_id})
    return {"status": "rejected"}


@router.post("/approve")
def approve(payload: ApproveRequest, session: Session = Depends(get_session), user: User = Depends(require_role(Role.ADMIN))):
    try:
        role = Role.from_str(payload.role)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")
    updated = approve_user_access(session, payload.user_id, role=role)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"status": "approved", "role": updated.role.value}


@router.delete("/pending/{user_id}")
def delete_pending(user_id: int, session: Session = Depends(get_session), user: User = Depends(require_role(Role.ADMIN))):
    deleted = delete_pending_user(session, user_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found or already approved")
    return {"status": "deleted"}
