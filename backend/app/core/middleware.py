import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.core.context import set_request_context

class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Extract headers (excluding sensitive ones like Authorization)
        headers = dict(request.headers)
        if "authorization" in headers:
            headers["authorization"] = "[REDACTED]"
        if "cookie" in headers:
            headers["cookie"] = "[REDACTED]"
            
        context_data = {
            "client_ip": request.client.host if request.client else None,
            "method": request.method,
            "path": request.url.path,
            "user_agent": headers.get("user-agent"),
            "headers": headers,
            "start_time": start_time
        }
        
        set_request_context(context_data)
        
        response = await call_next(request)
        
        return response
