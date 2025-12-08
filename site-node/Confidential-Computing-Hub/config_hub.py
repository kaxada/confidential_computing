# Confidential-Computing-Hub/config_hub.py
import os
from dotenv import load_dotenv

load_dotenv()

# We still need this to map IDs to URLs for the SiteManager
# But descriptions are gone! They live in the Vector DB now.
SITE_REGISTRY = {
    "site_1": {"url": os.getenv("SITE_1_URL", "http://localhost:8080")},
    "site_2": {"url": os.getenv("SITE_2_URL", "http://localhost:8081")},
    "site_3": {"url": os.getenv("SITE_3_URL", "http://localhost:8082")}
}

HUB_SECRET_KEY = os.getenv("HUB_SECRET_KEY", "hub_secret_key_123")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
AGGREGATION_MODEL = "gpt-4"