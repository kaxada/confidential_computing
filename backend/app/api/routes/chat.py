from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps.auth import require_approved
# from app.clients.site import send_query # Removed
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

# Hub Services
from app.services.router import router as hub_router
from app.services.site_manager import site_manager
from app.services.aggregator import aggregator
from app.core.token import token_issuer

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
async def chat_query(payload: ChatRequest, user: User = Depends(require_approved), session: Session = Depends(get_session)):
    if not payload.question or not payload.question.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question required")
    
    is_new_thread = payload.thread_id is None
    thread = get_or_create_thread(session, user_id=user.id, thread_id=payload.thread_id, title=payload.title)
    
    add_message(session, thread, user_id=user.id, role="user", content=payload.question)
    
    # Use the decoupled effective privacy level
    privacy_level = user.effective_privacy_level
    
    # We still pass a role for context, but privacy is explicit
    role_for_site = user.role.value if user.role else "student"
    
    # --- Hub Pipeline ---
    
    # 1. Generate Token
    token = token_issuer.generate_policy_token(
        user_id=user.id, role=role_for_site, privacy_level=privacy_level
    )
    
    # 2. Semantic Routing
    target_sites = hub_router.route_query(payload.question)
    
    if not target_sites:
        assistant_msg = "I couldn't find any relevant data sites for your specific query in the Hub Registry."
        result = {"response": assistant_msg, "status": "no_sites", "thread_id": thread.id, "title": thread.title}
    else:
        # 3. Execution
        site_results = await site_manager.execute_targeted_queries(target_sites, payload.question, token)
        
        # 4. Aggregation
        assistant_msg = aggregator.synthesize_results(payload.question, site_results)
        
        result = {
            "response": assistant_msg,
            "routed_to": target_sites,
            "status": "success",
            "thread_id": thread.id,
            "title": thread.title
        }
    
    log_event(session, user.id, "chat_query", {
        "privacy": privacy_level, 
        "routed_to": target_sites if 'target_sites' in locals() else [],
        "status": result.get("status")
    })

    add_message(session, thread, user_id=user.id, role="assistant", content=assistant_msg)

    # Auto-generate title if new thread
    if is_new_thread:
        try:
            new_title = aggregator.generate_title(payload.question, assistant_msg)
            update_thread(session, thread.id, user.id, new_title)
            result["title"] = new_title
        except Exception as e:
            log_event(session, user.id, "title_generation_error", {"error": str(e)})

    return result
