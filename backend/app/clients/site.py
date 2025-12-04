import requests
from typing import Optional

from app.core.config import settings


def send_query(question: str, role: str, user_id: int, privacy_level: Optional[str] = None) -> dict:
    """Send a query to the site-node server (FastAPI)."""
    payload = {
        "query": question,
        "role": role or "student",
        "privacy_level": privacy_level or settings.default_privacy_level,
        "user_id": str(user_id),
        "site_id": settings.site_id,
    }

    try:
        resp = requests.post(
            f"{settings.site_base_url}/query",
            json=payload,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception:
        # Offline stub keeps the hub happy while site/enclave is not up.
        return {
            "response": f"[stubbed answer] You asked: '{question}'. Role: {role}. Privacy: {payload['privacy_level']}",
            "metadata": {"stub": True},
            "status": "success",
        }
