from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from chromadb.utils import embedding_functions

from chromadb_revised_architecture import SiteRAGDatabase

# Initialize site DB (pointing to existing persisted DB path)
# Adjust db_path if the persisted DB is elsewhere
site_db = SiteRAGDatabase(site_name="site1", site_type="general", db_path="./chroma_site1_db")

# Override embedding function to avoid downloading in this stub (uses default inside class otherwise)
site_db.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

ROLE_PRIVACY = {
    "admin": "low",
    "researcher": "moderate",
    "default": "moderate",
}

app = FastAPI(title="Site RAG Service", version="0.1.0")


class QueryRequest(BaseModel):
    question: str
    role: str = "researcher"
    user_id: int


@app.post("/query")
def query(req: QueryRequest):
    privacy_level = ROLE_PRIVACY.get(req.role, ROLE_PRIVACY["default"])
    try:
        results = site_db.query(req.question, privacy_level=privacy_level, n_results=3)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    docs = (results or {}).get("results", {}).get("documents", [[]])
    first_doc = docs[0][0] if docs and docs[0] else ""
    answer = f"[site:{results.get('site','site1')} privacy:{privacy_level}] {first_doc}"
    return {"answer": answer, "source_docs": docs, "privacy_level": privacy_level}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9000)
