from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ChatMessage, ChatThread


def get_or_create_thread(session: Session, user_id: int, thread_id: Optional[int] = None, title: Optional[str] = None) -> ChatThread:
    if thread_id:
        thread = session.get(ChatThread, thread_id)
        if thread and thread.user_id == user_id:
            return thread
    thread = ChatThread(user_id=user_id, title=title)
    session.add(thread)
    session.commit()
    session.refresh(thread)
    return thread


def add_message(session: Session, thread: ChatThread, user_id: int, role: str, content: str) -> ChatMessage:
    msg = ChatMessage(thread_id=thread.id, user_id=user_id, role=role, content=content)
    session.add(msg)
    session.commit()
    session.refresh(msg)
    return msg


def list_threads(session: Session, user_id: int) -> List[ChatThread]:
    stmt = select(ChatThread).where(ChatThread.user_id == user_id).order_by(ChatThread.created_at.desc())
    return list(session.execute(stmt).scalars().all())


def list_messages(session: Session, user_id: int, thread_id: int) -> List[ChatMessage]:
    stmt = select(ChatMessage).where(ChatMessage.user_id == user_id, ChatMessage.thread_id == thread_id).order_by(ChatMessage.created_at)
    return list(session.execute(stmt).scalars().all())
