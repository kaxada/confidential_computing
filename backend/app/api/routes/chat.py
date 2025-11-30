from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps.auth import require_approved
from app.clients.site import send_query
from app.core.db import get_session
from app.models import User
from app.schemas import ChatRequest, MessageResponse, ThreadResponse
from app.services.chat import add_message, get_or_create_thread, list_messages, list_threads

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/threads", response_model=list[ThreadResponse])
def get_threads(user: User = Depends(require_approved), session: Session = Depends(get_session)):
    threads = list_threads(session, user.id)
    return [ThreadResponse(id=t.id, title=t.title) for t in threads]


@router.get("/threads/{thread_id}/messages", response_model=list[MessageResponse])
def get_thread_messages(thread_id: int, user: User = Depends(require_approved), session: Session = Depends(get_session)):
    msgs = list_messages(session, user.id, thread_id)
    return [MessageResponse(id=m.id, role=m.role, content=m.content) for m in msgs]


@router.post("/query")
def chat_query(payload: ChatRequest, user: User = Depends(require_approved), session: Session = Depends(get_session)):
    if not payload.question or not payload.question.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question required")
    thread = get_or_create_thread(session, user_id=user.id, thread_id=payload.thread_id, title=payload.title)
    add_message(session, thread, user_id=user.id, role="user", content=payload.question)
    result = send_query(question=payload.question, role=user.role.value if user.role else "", user_id=user.id)
    add_message(session, thread, user_id=user.id, role="assistant", content=result.get("answer", ""))
    return {**result, "thread_id": thread.id}
