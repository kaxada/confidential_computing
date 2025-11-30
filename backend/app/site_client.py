import requests

from .config import settings


def send_query(question: str, role: str, user_id: int) -> dict:
    # Try real site first; fall back to canned response if unavailable.
    try:
        resp = requests.post(
            f"{settings.site_base_url}/query",
            json={"question": question, "role": role, "user_id": user_id},
            timeout=5,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception:
        # Offline stub keeps the hub happy while site/enclave is not up.
        return {
            "answer": f"[stubbed answer] You asked: '{question}'. Role: {role}.",
            "source_docs": ["stub-doc-1"],
        }
