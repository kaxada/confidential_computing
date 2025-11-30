from fastapi import APIRouter, Depends, HTTPException, status

from .auth import require_approved
from .models import User
from .schemas import ChatRequest
from .site_client import send_query

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/query")
def chat_query(payload: ChatRequest, user: User = Depends(require_approved)):
    # Only approved users can hit chat; enforced by dependency.
    if not payload.question or not payload.question.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question required")
    result = send_query(question=payload.question, role=user.role.value if user.role else "", user_id=user.id)
    return result
