# config.py
# Configuration file for the distributed RAG system

import os
from dotenv import load_dotenv

load_dotenv()

# Base directory for relative paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- LLM Provider Configuration ---
# Choose provider: "openai" or "gemini"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # Default to OpenAI (cheaper)

# --- OpenAI Configuration ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
DEFAULT_OPENAI_MODEL = "gpt-4.1-nano"  # Cheapest model
OPENAI_GENERATION_CONFIG = {
    "temperature": 0.7,
    "max_tokens": 512,
    "top_p": 0.9,
}

# --- Google Gemini Configuration ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
# DEFAULT_GOOGLE_MODEL_ID = "gemini-1.5-flash"
# DEFAULT_GOOGLE_EMBEDDING_MODEL = "models/text-embedding-004"
DEFAULT_GOOGLE_GENERATION_CONFIG = {
    "temperature": 0.7,
    "top_p": 0.9,
    "max_output_tokens": 512,
}

# --- Vector Database API Configuration ---
VECTOR_DB_MODE = os.getenv("VECTOR_DB_MODE", "local").lower()  # "local" (default) or "http"

# Local ChromaDB configuration (default: use ./data persistent DB)
CHROMA_DB_PATH = os.getenv(
    "CHROMA_DB_PATH",
    os.path.abspath(os.path.join(BASE_DIR, "data/chromadb_site1_db"))
)
CHROMA_SITE_NAME = os.getenv("CHROMA_SITE_NAME", "site1")
CHROMA_COLLECTION_TEMPLATE = os.getenv("CHROMA_COLLECTION_TEMPLATE", "{site}_{privacy}_privacy")
DEFAULT_EMBEDDING_MODEL = os.getenv("DEFAULT_EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# Optional HTTP fallback (kept for compatibility)
VECTOR_DB_API_URL = os.getenv("VECTOR_DB_API_URL", "http://127.0.0.1:8000")
VECTOR_DB_QUERY_ENDPOINT = f"{VECTOR_DB_API_URL}/query"

# --- Privacy & Policy Configuration ---
# Privacy levels mapped to knowledge base access
PRIVACY_LEVEL_MAPPING = {
    "none": "none",      # Full access, no DP noise (for PIs/authorized researchers)
    "low": "low",        # Minimal DP noise (for site staff)
    "moderate": "moderate",  # Medium DP noise (for collaborators)
    "high": "high"       # Heavy DP noise (for students/external)
}

# Default privacy level if not specified in policy token
DEFAULT_PRIVACY_LEVEL = "moderate"

# Number of documents to retrieve from vector DB
DEFAULT_TOP_K = 3

# --- Policy Token Configuration ---
# In production, these would come from the central server's attestation
ENABLE_POLICY_VERIFICATION = os.getenv("ENABLE_POLICY_VERIFICATION", "false").lower() == "true"
POLICY_TOKEN_PUBLIC_KEY_PATH = os.getenv("POLICY_TOKEN_PUBLIC_KEY_PATH", "./keys/policy_public_key.pem")

# --- Knowledge Base Access Levels ---
# Defines which KB levels each role can access
ROLE_KB_ACCESS = {
    "student": ["KB1"],           # Most restricted, heavily anonymized
    "collaborator": ["KB1", "KB2"],  # Some access to less anonymized data
    "staff": ["KB1", "KB2", "KB3"],  # Site staff with more access
    "pi": ["KB1", "KB2", "KB3", "KB4"],  # Principal investigators, full access
    "researcher": ["KB1", "KB2", "KB3", "KB4"]  # Authorized researchers
}

# Default role if not specified
DEFAULT_ROLE = "student"

# --- Logging Configuration ---
DEFAULT_LOG_PATH = "./logs/chatbot.log"
DEFAULT_FLAGGED_PROMPTS_PATH = "./logs/flagged_prompts.csv"
DEFAULT_QUERY_LOG_PATH = "./logs/query_audit.log"

# --- Safety Configuration ---
# Emergency numbers by region
EMERGENCY_NUMBERS = {
    "US": "911",
    "UK": "999",
    "EU": "112",
    "AU": "000",
    "CA": "911",
    "default": "911 (US/Canada), 999 (UK), 112 (EU)"
}

# Crisis hotlines by region
CRISIS_HOTLINES = {
    "US": "988 (Suicide & Crisis Lifeline)",
    "UK": "111 (NHS) or 999 (emergency)",
    "CA": "988",
    "default": "988 (US/Canada) or 111 (UK)"
}

# Healthcare-specific safety settings
ENABLE_EMERGENCY_DETECTION = True
ENABLE_DIAGNOSIS_BLOCKING = True
ENABLE_DOSAGE_BLOCKING = True

# --- Enclave Configuration (for future deployment) ---
ENCLAVE_MODE = os.getenv("ENCLAVE_MODE", "false").lower() == "true"
ATTESTATION_ENDPOINT = os.getenv("ATTESTATION_ENDPOINT", "")
SITE_ID = os.getenv("SITE_ID", "site_local")

# --- PHI Scrubbing Configuration ---
ENABLE_PHI_SCRUBBING = True
PHI_REPLACEMENT_TOKEN = "[REDACTED]"
