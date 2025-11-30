from fastapi import APIRouter, Depends, HTTPException, status

from .auth import require_role
from .models import Role
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
def approve(user_id: int, role: Role, _: str = Depends(require_role(Role.ADMIN))):
    user = store.approve_user(user_id, role)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"status": "approved", "role": user.role.value}
