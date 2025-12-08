from typing import Optional

from pydantic import BaseModel


class SignupRequest(BaseModel):
    email: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    requested_role: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class ApproveRequest(BaseModel):
    user_id: int
    role: str


class ChatRequest(BaseModel):
    question: str
    thread_id: Optional[int] = None
    title: Optional[str] = None
    privacy_level: Optional[str] = None


class ThreadResponse(BaseModel):
    id: int
    title: Optional[str] = None


class ThreadUpdateRequest(BaseModel):
    title: str


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
