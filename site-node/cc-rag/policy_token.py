# policy_token.py
# Handles policy token verification and extraction for privacy-preserving RAG

import json
import logging
from dataclasses import dataclass
from typing import Optional, List
import config

# In production, this would use cryptographic verification
# For now, we'll use a simplified version for testing

@dataclass
class PolicyToken:
    """
    Represents a policy token sent from the central hub.
    Contains user role, allowed KB levels, and privacy budget.
    """
    user_id: str
    role: str
    allowed_kb_levels: List[str]
    privacy_level: str
    epsilon: float  # Privacy budget (DP parameter)
    site_id: str
    timestamp: str
    signature: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> 'PolicyToken':
        """Creates a PolicyToken from a dictionary."""
        return cls(
            user_id=data.get('user_id', 'anonymous'),
            role=data.get('role', config.DEFAULT_ROLE),
            allowed_kb_levels=data.get('allowed_kb_levels', config.ROLE_KB_ACCESS.get(config.DEFAULT_ROLE, ['KB1'])),
            privacy_level=data.get('privacy_level', config.DEFAULT_PRIVACY_LEVEL),
            epsilon=data.get('epsilon', 1.0),
            site_id=data.get('site_id', config.SITE_ID),
            timestamp=data.get('timestamp', ''),
            signature=data.get('signature')
        )

    def to_dict(self) -> dict:
        """Converts PolicyToken to dictionary."""
        return {
            'user_id': self.user_id,
            'role': self.role,
            'allowed_kb_levels': self.allowed_kb_levels,
            'privacy_level': self.privacy_level,
            'epsilon': self.epsilon,
            'site_id': self.site_id,
            'timestamp': self.timestamp,
            'signature': self.signature
        }


class PolicyTokenVerifier:
    """
    Verifies and validates policy tokens from the central hub.
    In production, this would verify cryptographic signatures.
    """
    
    def __init__(self):
        """Initialize the policy token verifier."""
        self.enable_verification = config.ENABLE_POLICY_VERIFICATION
        if self.enable_verification:
            logging.info("Policy token verification enabled")
        else:
            logging.info("Policy token verification disabled (testing mode)")

    def verify_token(self, token: PolicyToken) -> tuple[bool, Optional[str]]:
        """
        Verifies the authenticity and validity of a policy token.
        
        Args:
            token: The PolicyToken to verify
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # If verification is disabled (testing mode), accept all tokens
        if not self.enable_verification:
            return True, None

        # In production, verify cryptographic signature here
        if not token.signature:
            return False, "Missing signature in policy token"

        # Verify site ID matches
        if token.site_id != config.SITE_ID:
            return False, f"Token site_id {token.site_id} does not match site {config.SITE_ID}"

        # Verify role is valid
        if token.role not in config.ROLE_KB_ACCESS:
            return False, f"Invalid role: {token.role}"

        # Verify privacy level is valid
        if token.privacy_level not in config.PRIVACY_LEVEL_MAPPING:
            return False, f"Invalid privacy_level: {token.privacy_level}"

        # Verify epsilon is reasonable (not negative, not too large)
        if token.epsilon < 0 or token.epsilon > 10:
            return False, f"Privacy budget (epsilon) out of range: {token.epsilon}"

        return True, None

    def extract_token_from_request(self, request_data: dict) -> Optional[PolicyToken]:
        """
        Extracts a policy token from a request dictionary.
        
        Args:
            request_data: Dictionary containing request data
            
        Returns:
            PolicyToken if found and valid, None otherwise
        """
        try:
            # Policy token could be in the request under 'policy_token' key
            if 'policy_token' in request_data:
                token_data = request_data['policy_token']
                if isinstance(token_data, str):
                    token_data = json.loads(token_data)
                return PolicyToken.from_dict(token_data)
            
            # Or it could be flattened into the main request
            # Extract relevant fields
            token_data = {
                'user_id': request_data.get('user_id', 'anonymous'),
                'role': request_data.get('role', config.DEFAULT_ROLE),
                'privacy_level': request_data.get('privacy_level', config.DEFAULT_PRIVACY_LEVEL),
                'allowed_kb_levels': request_data.get('allowed_kb_levels'),
                'epsilon': request_data.get('epsilon', 1.0),
                'site_id': request_data.get('site_id', config.SITE_ID),
                'timestamp': request_data.get('timestamp', ''),
                'signature': request_data.get('signature')
            }
            
            # If allowed_kb_levels not provided, derive from role
            if not token_data['allowed_kb_levels']:
                token_data['allowed_kb_levels'] = config.ROLE_KB_ACCESS.get(
                    token_data['role'], 
                    ['KB1']
                )
            
            return PolicyToken.from_dict(token_data)
            
        except Exception as e:
            logging.error(f"Error extracting policy token: {e}")
            return None


def create_default_token(privacy_level: str = None, role: str = None) -> PolicyToken:
    """
    Creates a default policy token for local testing.
    
    Args:
        privacy_level: Privacy level to use (defaults to config default)
        role: User role to use (defaults to config default)
        
    Returns:
        A default PolicyToken
    """
    role = role or config.DEFAULT_ROLE
    privacy_level = privacy_level or config.DEFAULT_PRIVACY_LEVEL
    
    return PolicyToken(
        user_id="local_test_user",
        role=role,
        allowed_kb_levels=config.ROLE_KB_ACCESS.get(role, ['KB1']),
        privacy_level=privacy_level,
        epsilon=1.0,
        site_id=config.SITE_ID,
        timestamp="",
        signature=None
    )