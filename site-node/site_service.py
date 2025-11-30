import re
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import pandas as pd
import pandas as pd

USE_CHROMA = False
DATA_CSV = "./site1_medical_data_large.csv"

if USE_CHROMA:
    from chromadb.utils import embedding_functions
    from chromadb_revised_architecture import SiteRAGDatabase

    site_db = SiteRAGDatabase(site_name="site1", site_type="general", db_path="./chroma_site1_db")
    # Populate Chroma if empty
    if not site_db.collections.get("moderate") or site_db.collections["moderate"].count() == 0:
        try:
            site_db.process_and_store(DATA_CSV)
        except Exception as exc:
            print(f"[WARN] Failed to process and store data: {exc}")

    site_db.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
else:
    site_db = None

# Load raw CSV for fallback responses
try:
    df = pd.read_csv(DATA_CSV)
except Exception as exc:
    print(f"[WARN] Could not load CSV for fallback: {exc}")
    df = None

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


def fallback_answer(question: str, privacy_level: str):
    if df is None or df.empty:
        raise HTTPException(status_code=500, detail="Site data unavailable")
    tokens = [t for t in re.split(r"\W+", question.lower()) if len(t) > 3]
    row = None
    if tokens:
        for _, r in df.iterrows():
            notes = str(r.get("notes", "")).lower()
            if any(tok in notes for tok in tokens):
                row = r
                break
    if row is None:
        row = df.iloc[0]

    notes = str(row.get("notes", "")) or ""
    phi = str(row.get("phi_elements", "")) or ""
    for item in phi.split("|"):
        if ":" in item:
            _, val = item.split(":", 1)
            notes = notes.replace(val, "[REDACTED]")

    diag = row.get("diagnosis_description", "") or row.get("chief_complaint", "") or "record"
    answer = f"[site:site1 privacy:{privacy_level}] {diag}. Notes: {notes}"
    return {"answer": answer, "source_docs": [notes], "privacy_level": privacy_level}


@app.post("/query")
def query(req: QueryRequest):
    privacy_level = ROLE_PRIVACY.get(req.role, ROLE_PRIVACY["default"])
    if USE_CHROMA and site_db:
        try:
            results = site_db.query(req.question, privacy_level=privacy_level, n_results=3)
            if results and results.get("results"):
                docs = results["results"].get("documents", [[]])
                first_doc = docs[0][0] if docs and docs[0] else ""
                answer = f"[site:{results.get('site','site1')} privacy:{privacy_level}] {first_doc}"
                return {"answer": answer, "source_docs": docs, "privacy_level": privacy_level}
        except Exception as exc:
            print(f"[WARN] Chroma query failed: {exc}")

    return fallback_answer(req.question, privacy_level)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9000)
