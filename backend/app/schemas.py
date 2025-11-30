from typing import Optional

from pydantic import BaseModel


class SignupRequest(BaseModel):
    email: str
    password: str
    requested_role: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class ApproveRequest(BaseModel):
    user_id: int
    role: str


class ChatRequest(BaseModel):
    question: str
