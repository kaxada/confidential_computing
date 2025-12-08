from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from app.models import UserLog
import json

def log_event(session: Session, user_id: int, event: str, details: Optional[dict] = None):
    """Log a user event."""
    log_entry = UserLog(
        user_id=user_id,
        event=event,
        details=json.dumps(details) if details else None,
        created_at=datetime.utcnow()
    )
    session.add(log_entry)
    session.commit()
