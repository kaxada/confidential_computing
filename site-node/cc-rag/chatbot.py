# chatbot.py
# Updated chatbot with policy token support for distributed RAG

from safety_guard import SafetyGuard
from rag_responder import RAGResponder 
from policy_token import PolicyToken, PolicyTokenVerifier, create_default_token
import logging
import config
import os
import csv
import datetime

# --- Logging Configuration ---
os.makedirs(os.path.dirname(config.DEFAULT_LOG_PATH), exist_ok=True)
logging.basicConfig(
    filename=config.DEFAULT_LOG_PATH, 
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class Chatbot:
    """
    The main class for the privacy-preserving healthcare chatbot.
    Manages conversation history, integrates safety guard and policy verification,
    and generates responses using the distributed RAG pipeline.
    """
    
    def __init__(self):
        """
        Initializes the chatbot with safety guard, policy verifier,
        RAG responder, and conversation history.
        """
        self.safety_guard = SafetyGuard()
        self.policy_verifier = PolicyTokenVerifier()
        self.responder = RAGResponder()
        self.history = []
        self.current_policy_token = None
        
        logging.info(f"Chatbot initialized for site: {config.SITE_ID}")
        logging.info(f"Enclave mode: {config.ENCLAVE_MODE}")

    def get_initial_greeting(self) -> str:
        """
        Returns the initial welcome and disclaimer message.
        """
        return (
            "Hello. I'm a healthcare information assistant. I can help you understand general "
            "health topics and medical information. \n\n"
            "Important: I am NOT a substitute for professional medical advice, diagnosis, or treatment. "
            "Always consult with qualified healthcare providers for medical decisions. \n\n"
            "For medical emergencies, call 911 (US/Canada), 999 (UK), or your local emergency number immediately."
        )

    def set_policy_token(self, token: PolicyToken) -> tuple[bool, str]:
        """
        Sets the policy token for the current session.
        Verifies the token before accepting it.
        
        Args:
            token: PolicyToken from the central hub
            
        Returns:
            Tuple of (success, message)
        """
        # Verify the token
        is_valid, error_msg = self.policy_verifier.verify_token(token)
        
        if not is_valid:
            logging.error(f"Invalid policy token: {error_msg}")
            return False, f"Policy token verification failed: {error_msg}"
        
        self.current_policy_token = token
        logging.info(f"Policy token set: role={token.role}, privacy_level={token.privacy_level}, site={token.site_id}")
        return True, "Policy token accepted"

    def get_response(self, user_input: str, policy_token: PolicyToken = None) -> str:
        """
        Processes user input with privacy and safety controls.
        
        Args:
            user_input: The text entered by the user
            policy_token: Optional policy token (if not set via set_policy_token)
            
        Returns:
            A string containing the bot's response
        """
        # Use provided token, or fall back to current session token, or create default
        token = policy_token or self.current_policy_token or create_default_token()
        
        # If a new token is provided, verify and set it
        if policy_token and policy_token != self.current_policy_token:
            success, msg = self.set_policy_token(policy_token)
            if not success:
                return f"Access denied: {msg}"
        
        # 1. Check the prompt with the safety guard
        is_safe, safety_response = self.safety_guard.check_prompt(user_input, self.history)
        
        if not is_safe:
            # If the prompt is unsafe, return the canned safety response
            response = safety_response
            log_flagged_prompt(user_input, response, token)
        else:
            # 2. If the prompt is safe, generate a response using the RAG pipeline
            response = self.responder.generate(user_input, token)
        
        # 3. Update the history
        self.history.append({
            "user": user_input, 
            "bot": response,
            "policy_token": token.to_dict()
        })
        
        # 4. Log the interaction with privacy info
        log_query(user_input, response, token)
        
        # 5. Trim history if too long
        if len(self.history) > 10:
            self.history.pop(0)
        
        return response

    def get_response_dict(self, user_input: str, policy_token: PolicyToken = None) -> dict:
        """
        Returns a structured response with metadata (useful for API endpoints).
        
        Args:
            user_input: The text entered by the user
            policy_token: Optional policy token
            
        Returns:
            Dictionary containing response, metadata, and status
        """
        token = policy_token or self.current_policy_token or create_default_token()
        
        response_text = self.get_response(user_input, token)
        
        return {
            "response": response_text,
            "metadata": {
                "site_id": config.SITE_ID,
                "privacy_level": token.privacy_level,
                "role": token.role,
                "timestamp": datetime.datetime.now().isoformat()
            },
            "status": "success"
        }


def log_flagged_prompt(user_input: str, response: str, policy_token: PolicyToken):
    """
    Logs unsafe user input into a CSV file with policy information.
    """
    os.makedirs(os.path.dirname(config.DEFAULT_FLAGGED_PROMPTS_PATH), exist_ok=True)
    
    file_exists = os.path.isfile(config.DEFAULT_FLAGGED_PROMPTS_PATH)
    
    with open(config.DEFAULT_FLAGGED_PROMPTS_PATH, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        
        if not file_exists:
            writer.writerow([
                "timestamp", "site_id", "user_id", "role", 
                "privacy_level", "user_input", "bot_response"
            ])
        
        writer.writerow([
            datetime.datetime.now().isoformat(),
            config.SITE_ID,
            policy_token.user_id,
            policy_token.role,
            policy_token.privacy_level,
            user_input,
            response
        ])


def log_query(user_input: str, response: str, policy_token: PolicyToken):
    """
    Logs queries to an audit log for compliance tracking.
    """
    os.makedirs(os.path.dirname(config.DEFAULT_QUERY_LOG_PATH), exist_ok=True)
    
    logging.info(
        f"QUERY_AUDIT | site={config.SITE_ID} | user={policy_token.user_id} | "
        f"role={policy_token.role} | privacy={policy_token.privacy_level} | "
        f"query_len={len(user_input)} | response_len={len(response)}"
    )