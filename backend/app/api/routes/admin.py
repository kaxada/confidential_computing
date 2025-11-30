from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps.auth import require_role
from app.core.db import get_session
from app.models import Role, User
from app.schemas import ApproveRequest
from app.services.user import approve_user, list_pending_users

router = APIRouter(prefix="/admin", tags=["admin"])


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
        role = Role(payload.role)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")
    updated = approve_user(session, payload.user_id, role)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"status": "approved", "role": updated.role.value}
