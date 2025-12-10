import time
from app.core.config import settings

class TokenIssuer:
    def __init__(self):
        pass

    def generate_policy_token(self, user_id: str, role: str, privacy_level: str) -> dict:
        """
        Generates the policy token payload.
        """
        return {
            "user_id": str(user_id),
            "role": role,
            "privacy_level": privacy_level,
            "timestamp": time.time(),
            "site_id": settings.site_id,
            "iss": "central_hub"
        }

token_issuer = TokenIssuer()
