from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps.auth import require_approved
from app.clients.site import send_query
from app.core.db import get_session
from app.models import User
from app.schemas import ChatRequest, MessageResponse, ThreadResponse, ThreadUpdateRequest
from app.services.chat import (
    add_message,
    delete_thread,
    get_or_create_thread,
    list_messages,
    list_threads,
    update_thread,
)
from app.services.log import log_event

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/threads", response_model=list[ThreadResponse])
def get_threads(user: User = Depends(require_approved), session: Session = Depends(get_session)):
    threads = list_threads(session, user.id)
    return [ThreadResponse(id=t.id, title=t.title) for t in threads]


@router.patch("/threads/{thread_id}", response_model=ThreadResponse)
def update_thread_title(
    thread_id: int,
    payload: ThreadUpdateRequest,
    user: User = Depends(require_approved),
    session: Session = Depends(get_session),
):
    thread = update_thread(session, thread_id, user.id, payload.title)
    if not thread:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")
    return ThreadResponse(id=thread.id, title=thread.title)


@router.delete("/threads/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_thread_endpoint(
    thread_id: int, user: User = Depends(require_approved), session: Session = Depends(get_session)
):
    success = delete_thread(session, thread_id, user.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/threads/{thread_id}/messages", response_model=list[MessageResponse])
def get_thread_messages(thread_id: int, user: User = Depends(require_approved), session: Session = Depends(get_session)):
    msgs = list_messages(session, user.id, thread_id)
    return [MessageResponse(id=m.id, role=m.role, content=m.content) for m in msgs]


@router.post("/query")
def chat_query(payload: ChatRequest, user: User = Depends(require_approved), session: Session = Depends(get_session)):
    if not payload.question or not payload.question.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question required")
    
    is_new_thread = payload.thread_id is None
    thread = get_or_create_thread(session, user_id=user.id, thread_id=payload.thread_id, title=payload.title)
    
    add_message(session, thread, user_id=user.id, role="user", content=payload.question)
    
    role_for_site = user.role.value if user.role else "student"
    result = send_query(
        question=payload.question,
        role=role_for_site,
        user_id=user.id,
        privacy_level=payload.privacy_level,
    )
    
    log_event(session, user.id, "chat_query", {"site_id": result.get("site_id"), "privacy": payload.privacy_level})

    assistant_msg = result.get("response") or result.get("answer") or ""
    add_message(session, thread, user_id=user.id, role="assistant", content=assistant_msg)

    # Auto-generate title if new thread
    if is_new_thread:
        try:
            title_prompt = (
                f"Summarize the following conversation into a short title (3-5 words). "
                f"Do not use quotes or prefixes like 'Title:'.\n\n"
                f"User: {payload.question}\nAssistant: {assistant_msg}"
            )
            title_res = send_query(
                question=title_prompt,
                role=role_for_site,
                user_id=user.id,
                privacy_level=payload.privacy_level,
            )
            new_title = title_res.get("response") or title_res.get("answer")
            if new_title:
                new_title = new_title.strip().strip('"').strip("'")
                if len(new_title) > 50:
                    new_title = new_title[:47] + "..."
                
                thread.title = new_title
                session.add(thread)
                session.commit()
        except Exception:
            pass

    return {**result, "thread_id": thread.id, "title": thread.title}
