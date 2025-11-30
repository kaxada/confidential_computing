import hashlib
import hmac
import itertools
from typing import Dict, List, Optional

from .models import Role, User


class InMemoryStore:
    def __init__(self):
        # Simple in-memory DB; swap for real persistence later.
        self._id_gen = itertools.count(1)
        self._users: Dict[int, User] = {}
        # Seed an admin for bootstrapping.
        self.create_user("admin@example.com", "admin", Role.ADMIN, approved=True, role=Role.ADMIN)

    def reset(self):
        # Reset state for tests; re-seed admin.
        self._id_gen = itertools.count(1)
        self._users = {}
        self.create_user("admin@example.com", "admin", Role.ADMIN, approved=True, role=Role.ADMIN)

    def _hash_password(self, password: str) -> str:
        # Demo-grade hashing; replace with bcrypt/argon2 in real use later.
        return hashlib.sha256(password.encode()).hexdigest()

    def _check_password(self, password: str, password_hash: str) -> bool:
        computed = hashlib.sha256(password.encode()).hexdigest()
        return hmac.compare_digest(computed, password_hash)

    def create_user(self, email: str, password: str, requested_role: Role, approved: bool = False, role: Optional[Role] = None) -> User:
        user_id = next(self._id_gen)
        user = User(
            id=user_id,
            email=email.lower(),
            password_hash=self._hash_password(password),
            requested_role=requested_role,
            role=role,
            approved=approved,
        )
        self._users[user_id] = user
        return user

    def get_by_email(self, email: str) -> Optional[User]:
        email = email.lower()
        return next((u for u in self._users.values() if u.email == email), None)

    def get_pending(self) -> List[User]:
        return [u for u in self._users.values() if not u.approved]

    def approve_user(self, user_id: int, role: Role) -> Optional[User]:
        user = self._users.get(user_id)
        if not user:
            return None
        user.role = role
        user.approved = True
        self._users[user_id] = user
        return user

    def verify_credentials(self, email: str, password: str) -> Optional[User]:
        user = self.get_by_email(email)
        if not user:
            return None
        if not self._check_password(password, user.password_hash):
            return None
        return user


store = InMemoryStore()
