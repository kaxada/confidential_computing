import time
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from app.models import UserLog
import json
from app.core.context import get_request_context

def log_event(session: Session, user_id: int, event: str, details: Optional[dict] = None):
    """Log a user event."""
    metadata = get_request_context()
    if metadata:
        # Create a copy to avoid mutating the context var directly (though it returns a dict ref)
        metadata = metadata.copy()
        if "start_time" in metadata:
            duration = (time.time() - metadata.pop("start_time")) * 1000 # ms
            metadata["duration_ms"] = round(duration, 2)
    
    log_entry = UserLog(
        user_id=user_id,
        event=event,
        details=json.dumps(details) if details else None,
        request_metadata=json.dumps(metadata) if metadata else None,
        created_at=datetime.utcnow()
    )
    session.add(log_entry)
    session.commit()
