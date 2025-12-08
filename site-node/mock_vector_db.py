# Confidential-Computing-RAG/mock_vector_db.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
import uvicorn

app = FastAPI(title="Mock Vector DB", description="Local In-Memory Vector Store for Testing")

# In-memory storage for our synthetic data
DOCUMENT_STORE = []

class QueryRequest(BaseModel):
    query_text: str
    privacy_level: str
    n_results: int = 3

class DocModel(BaseModel):
    content: str
    metadata: Dict

@app.get("/health")
def health_check():
    return {"status": "healthy", "count": len(DOCUMENT_STORE)}

@app.post("/add_documents")
def add_documents(docs: List[DocModel]):
    """
    Endpoint to ingest data (used by populate_sites.py)
    """
    global DOCUMENT_STORE
    for doc in docs:
        # Simple structure matching what the client expects
        entry = {
            "text": doc.content,
            "metadata": doc.metadata,
            "distance": 0.1  # Fake distance for scoring
        }
        DOCUMENT_STORE.append(entry)
    return {"status": "success", "added": len(docs)}

@app.post("/query")
def query_db(request: QueryRequest):
    """
    Returns documents based on simple keyword matching (Mock RAG)
    """
    results = []
    q_lower = request.query_text.lower()
    
    # Filter by source/type if present in query (rudimentary routing simulation)
    # In a real DB, this would use vector embeddings.
    for doc in DOCUMENT_STORE:
        # A simple "contains" search to mimic retrieval
        # If the DB is empty, or query matches nothing, we return nothing.
        # For testing, we can be generous: if DB is small, return everything relevant.
        if len(DOCUMENT_STORE) < 20 or q_lower in doc["text"].lower():
            results.append(doc)

    # Apply limits
    return {"results": results[:request.n_results]}

if __name__ == "__main__":
    # Runs on port 8000, which is where your Sites look for the DB
    uvicorn.run(app, host="0.0.0.0", port=8000)