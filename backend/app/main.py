from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.admin import router as admin_router
from app.api.routes.auth import router as auth_router
from app.api.routes.chat import router as chat_router
from app.core import db
from app.services.user import init_admin

app = FastAPI(title="Confidential RAG Hub", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    # Create tables if not exist and seed admin.
    db.Base.metadata.create_all(bind=db.engine)
    with db.SessionLocal() as session:
        init_admin(session)

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(chat_router)


@app.get("/health")
def health():
    return {"status": "ok"}
