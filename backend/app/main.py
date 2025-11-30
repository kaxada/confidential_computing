from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes_admin import router as admin_router
from .routes_auth import router as auth_router
from .routes_chat import router as chat_router

app = FastAPI(title="Confidential RAG Hub", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(chat_router)


@app.get("/health")
def health():
    return {"status": "ok"}
