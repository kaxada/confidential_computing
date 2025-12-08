# token_issuer.py
import jwt
import time
import config_hub

class TokenIssuer:
    def __init__(self):
        self.secret = config_hub.HUB_SECRET_KEY

    def generate_policy_token(self, user_id: str, role: str, privacy_level: str) -> dict:
        """
        Generates the 'CC Attestation' token shown in the diagram bubbles.
        Sites verify this to ensure the request is from a valid Hub.
        """
        
        # Rule-based Access Control Logic
        # Defines which KB levels each role can access (KB1-KB4)
        role_kb_map = {
            "student": ["KB1"],
            "collaborator": ["KB1", "KB2"],
            "staff": ["KB1", "KB2", "KB3"],
            "pi": ["KB1", "KB2", "KB3", "KB4"],
            "researcher": ["KB1", "KB2", "KB3", "KB4"]
        }
        
        payload = {
            "user_id": user_id,
            "role": role,
            "privacy_level": privacy_level,
            "allowed_kb_levels": role_kb_map.get(role, ["KB1"]),
            "epsilon": 1.0,  # Privacy budget
            "timestamp": time.time(),
            "site_id": "hub_central",
            "iss": "central_hub"
        }
        
        # Sign the token (HS256 for testing, RS256 for production)
        signature = jwt.encode(payload, self.secret, algorithm="HS256")
        
        # Attach signature for the site to verify
        payload['signature'] = signature
        return payload