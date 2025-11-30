from fastapi import APIRouter, Depends, HTTPException, status

from .auth import require_role
from .models import Role
from .schemas import ApproveRequest
from .store import store

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/pending")
def list_pending(_: str = Depends(require_role(Role.ADMIN))):
    pending = store.get_pending()
    return [
        {"id": u.id, "email": u.email, "requested_role": u.requested_role.value}
        for u in pending
    ]


@router.post("/approve")
def approve(payload: ApproveRequest, _: str = Depends(require_role(Role.ADMIN))):
    try:
        role = Role(payload.role)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")
    user = store.approve_user(payload.user_id, role)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"status": "approved", "role": user.role.value}
