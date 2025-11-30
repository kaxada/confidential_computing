from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Role(str, Enum):
    ADMIN = "admin"
    RESEARCHER = "researcher"


@dataclass
class User:
    id: int
    email: str
    password_hash: str
    requested_role: Role
    role: Optional[Role]
    approved: bool
