from contextvars import ContextVar
from typing import Optional, Dict, Any

_request_context_var: ContextVar[Optional[Dict[str, Any]]] = ContextVar("request_context", default=None)

def set_request_context(context: Dict[str, Any]):
    _request_context_var.set(context)

def get_request_context() -> Optional[Dict[str, Any]]:
    return _request_context_var.get()
