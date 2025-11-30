from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Stub Site RAG Service", version="0.1.0")


class QueryRequest(BaseModel):
    question: str
    role: str
    user_id: int


@app.post("/query")
def query(body: QueryRequest):
    # Echo back a canned response; replace with enclave call later.
    return {
        "answer": f"[stub site] User {body.user_id} ({body.role}) asked: '{body.question}'",
        "source_docs": ["stub-doc-1", "stub-doc-2"],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9000)
