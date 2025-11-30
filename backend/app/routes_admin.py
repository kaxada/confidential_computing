from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .auth import require_role
from .db import get_session
from .models import Role
from .schemas import ApproveRequest
from .services import approve_user, list_pending_users

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/pending")
def list_pending(session: Session = Depends(get_session), _: str = Depends(require_role(Role.ADMIN))):
    pending = list_pending_users(session)
    return [
        {"id": u.id, "email": u.email, "requested_role": u.requested_role.value}
        for u in pending
    ]


@router.post("/approve")
def approve(payload: ApproveRequest, session: Session = Depends(get_session), _: str = Depends(require_role(Role.ADMIN))):
    try:
        role = Role(payload.role)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")
    user = approve_user(session, payload.user_id, role)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"status": "approved", "role": user.role.value}
