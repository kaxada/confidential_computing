#!/usr/bin/env python3
"""
FastAPI RAG Service for Site1
- Loads existing ChromaDB persistent collections
- Provides query endpoint with async support
- Adds simple logging/auditing
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from chromadb import PersistentClient
from chromadb.utils import embedding_functions
import logging
import os
from datetime import datetime

# ---------------------------
# Logging / Auditing Setup
# ---------------------------
LOG_FILE = "./rag_queries.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

def audit_query(query: str, privacy_level: str, n_results: int):
    logging.info(f"Query: {query} | Privacy: {privacy_level} | n_results: {n_results}")

# ---------------------------
# FastAPI App
# ---------------------------
app = FastAPI(title="Site1 RAG Service", version="1.0")

# ---------------------------
# ChromaDB Client & Collections
# ---------------------------
DB_PATH = './chromadb_site1_db'
PRIVACY_LEVELS = ['none', 'low', 'moderate', 'high']

print("🚀 Loading embedding model and persistent ChromaDB client...")
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)
client = PersistentClient(path=DB_PATH)

collections = {}
for level in PRIVACY_LEVELS:
    col_name = f"site1_{level}_privacy"
    try:
        collections[level] = client.get_collection(name=col_name)
        print(f"Loaded collection: {col_name}")
    except Exception as e:
        print(f"Error loading collection {col_name}: {e}")
        collections[level] = None

# ---------------------------
# Request / Response Models
# ---------------------------
class QueryRequest(BaseModel):
    query_text: str
    privacy_level: Optional[str] = 'moderate'
    n_results: Optional[int] = 3

class QueryResponseItem(BaseModel):
    text: str
    metadata: dict

class QueryResponse(BaseModel):
    results: List[QueryResponseItem]

# ---------------------------
# Query Endpoint
# ---------------------------
@app.post("/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    if request.privacy_level not in collections or collections[request.privacy_level] is None:
        raise HTTPException(status_code=400, detail="Invalid privacy level or collection not loaded")
    col = collections[request.privacy_level]

    # Audit
    audit_query(request.query_text, request.privacy_level, request.n_results)

    try:
        result = col.query(query_texts=[request.query_text], n_results=request.n_results)
        documents = result['documents'][0]
        metadatas = result['metadatas'][0]
        response_items = [QueryResponseItem(text=doc, metadata=meta) for doc, meta in zip(documents, metadatas)]
        return QueryResponse(results=response_items)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------
# Health Check Endpoint
# ---------------------------
@app.get("/health")
async def health_check():
    return {"status": "ok", "collections_loaded": list(collections.keys())}
