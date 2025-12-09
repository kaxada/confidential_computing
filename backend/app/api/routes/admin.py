from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps.auth import require_role
from app.core.db import get_session
from app.models import Role, User, UserLog
from app.schemas import AdminRoleUpdateRequest, ApproveRequest
from app.services.log import log_event
from app.services.user import (
    approve_user,
    delete_pending_user,
    delete_user_and_threads,
    list_all_users,
    list_pending_users,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users")
def get_all_users(session: Session = Depends(get_session), user: User = Depends(require_role(Role.ADMIN))):
    users = list_all_users(session)
    return [
        {
            "id": u.id,
            "email": u.email,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "role": u.role.value if u.role else None,
            "base_role": u.role.value if u.role else None,
            "requested_role": u.requested_role.value,
            "role_expires_at": u.role_expires_at,
            "request_reason": u.request_reason,
            "approved": u.approved,
        }
        for u in users
    ]


@router.get("/logs")
def get_logs(session: Session = Depends(get_session), user: User = Depends(require_role(Role.ADMIN))):
    stmt = select(UserLog).order_by(UserLog.created_at.desc()).limit(100)
    logs = session.execute(stmt).scalars().all()
    return [
        {
            "id": l.id,
            "user_id": l.user_id,
            "event": l.event,
            "details": l.details,
            "created_at": l.created_at,
        }
        for l in logs
    ]


@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    payload: AdminRoleUpdateRequest,
    session: Session = Depends(get_session),
    admin: User = Depends(require_role(Role.ADMIN)),
):
    try:
        role = Role.from_str(payload.role)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")
    
    expires_at = payload.expires_at
    if payload.duration_minutes is not None:
        if not (0.25 <= payload.duration_minutes <= 60):
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Duration must be between 0.25 and 60 minutes")
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=payload.duration_minutes)

    updated = approve_user(session, user_id, role, expires_at)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    log_event(session, admin.id, "admin_update_role", {
        "target_user_id": user_id, 
        "new_role": role.value,
        "duration": payload.duration_minutes,
        "expires_at": str(expires_at) if expires_at else None
    })
    return {"status": "updated", "role": updated.role.value, "expires_at": updated.role_expires_at}


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
    pending = list_pending_users(session)
    return [
        {"id": u.id, "email": u.email, "requested_role": u.requested_role.value}
        for u in pending
    ]


@router.post("/approve")
def approve(payload: ApproveRequest, session: Session = Depends(get_session), user: User = Depends(require_role(Role.ADMIN))):
    try:
        role = Role.from_str(payload.role)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")
    updated = approve_user(session, payload.user_id, role)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"status": "approved", "role": updated.role.value}


@router.delete("/pending/{user_id}")
def delete_pending(user_id: int, session: Session = Depends(get_session), user: User = Depends(require_role(Role.ADMIN))):
    deleted = delete_pending_user(session, user_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found or already approved")
    return {"status": "deleted"}
