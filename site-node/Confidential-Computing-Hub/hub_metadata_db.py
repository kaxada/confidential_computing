# Confidential-Computing-Hub/hub_metadata_db.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import numpy as np
from openai import OpenAI
import os
from dotenv import load_dotenv
import uvicorn

load_dotenv()

app = FastAPI(title="Hub Metadata Store", description="Vector DB for Site Routing")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# In-Memory Vector Store
# Structure: [{"vector": np.array, "metadata": dict, "text": str}]
VECTOR_STORE = []

class Document(BaseModel):
    text: str
    metadata: Dict[str, Any]

class Query(BaseModel):
    query_text: str
    n_results: int = 1

def get_embedding(text: str):
    """Generates vector embedding using OpenAI"""
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small" # Efficient, cheap model
    )
    return response.data[0].embedding

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

@app.post("/add_site")
def add_site_profile(doc: Document):
    """
    Adds a site description to the registry.
    """
    vector = get_embedding(doc.text)
    VECTOR_STORE.append({
        "vector": vector,
        "metadata": doc.metadata,
        "text": doc.text
    })
    return {"status": "success", "site_id": doc.metadata.get("site_id")}

@app.post("/search")
def find_relevant_sites(query: Query):
    """
    Semantic Search: Finds the site description closest to the user query.
    """
    if not VECTOR_STORE:
        return {"results": []}

    query_vector = get_embedding(query.query_text)
    
    # Calculate scores
    scored_results = []
    for item in VECTOR_STORE:
        score = cosine_similarity(query_vector, item["vector"])
        scored_results.append({
            "score": score,
            "site_id": item["metadata"]["site_id"],
            "url": item["metadata"]["url"],
            "description": item["text"]
        })
    
    # Sort by score (highest first)
    scored_results.sort(key=lambda x: x["score"], reverse=True)
    
    # Filter: Only return results with decent similarity (e.g., > 0.3)
    # This prevents routing to irrelevant sites if the query is nonsense.
    final_results = [r for r in scored_results if r["score"] > 0.3][:query.n_results]
    
    return {"results": final_results}

if __name__ == "__main__":
    # Runs on Port 9001 (Distinct from Hub on 9000 and Sites on 8080+)
    uvicorn.run(app, host="0.0.0.0", port=9001)