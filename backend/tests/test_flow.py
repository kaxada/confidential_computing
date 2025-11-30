import pytest
from fastapi.testclient import TestClient

from app.core import db
from app.main import app
from app.services.user import init_admin


def setup_function():
    db.Base.metadata.drop_all(bind=db.engine)
    db.Base.metadata.create_all(bind=db.engine)
    with db.SessionLocal() as session:
        init_admin(session)


def test_signup_approval_login_and_chat():
    client = TestClient(app)

    # Signup creates pending user
    resp = client.post("/auth/signup", json={"email": "alice@example.com", "password": "pass123"})
    assert resp.status_code == 201
    assert resp.json()["status"] == "pending"

    # Login fails while pending
    resp = client.post("/auth/login", json={"email": "alice@example.com", "password": "pass123"})
    assert resp.status_code == 403

    # Admin login
    resp = client.post("/auth/login", json={"email": "admin@example.com", "password": "admin"})
    assert resp.status_code == 200
    admin_token = resp.json()["token"]

    # Pending list shows the new user
    resp = client.get("/admin/pending", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    pending = resp.json()
    assert any(u["email"] == "alice@example.com" for u in pending)
    user_id = next(u["id"] for u in pending if u["email"] == "alice@example.com")

    # Approve user
    resp = client.post(
        "/admin/approve",
        json={"user_id": user_id, "role": "researcher"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200

    # Login works after approval
    resp = client.post("/auth/login", json={"email": "alice@example.com", "password": "pass123"})
    assert resp.status_code == 200
    user_token = resp.json()["token"]

    # Chat returns stub response and creates thread/messages
    resp = client.post(
        "/chat/query",
        json={"question": "Hello?"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    thread_id = data.get("thread_id")
    assert thread_id is not None

    # Fetch threads
    resp = client.get("/chat/threads", headers={"Authorization": f"Bearer {user_token}"})
    assert resp.status_code == 200
    threads = resp.json()
    assert any(t["id"] == thread_id for t in threads)

    # Fetch messages
    resp = client.get(f"/chat/threads/{thread_id}/messages", headers={"Authorization": f"Bearer {user_token}"})
    assert resp.status_code == 200
    msgs = resp.json()
    assert len(msgs) == 2  # user question + assistant answer
