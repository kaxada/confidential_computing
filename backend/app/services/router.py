from typing import List
import numpy as np
from openai import OpenAI
from app.core.config import settings
import logging

class HubRouter:
    """
    Semantic Router using In-Memory Vector Search.
    """
    def __init__(self):
        self.vector_store = []
        self.client = None
        self._initialized = False

    def _get_client(self):
        if not self.client and settings.openai_api_key:
            self.client = OpenAI(api_key=settings.openai_api_key)
        return self.client

    def _get_embedding(self, text: str):
        client = self._get_client()
        if not client:
            return None

        try:
            response = client.embeddings.create(
                input=text,
                model="text-embedding-3-small"
            )
            return response.data[0].embedding
        except Exception as e:
            logging.error(f"Embedding error: {e}")
            return None

    def initialize_store(self):
        """Populate the vector store from config metadata."""
        if self._initialized:
            return

        if not settings.openai_api_key:
            logging.warning("Skipping Router initialization: No OpenAI Key")
            return

        logging.info("Initializing Semantic Router...")
        for item in settings.site_metadata:
            vector = self._get_embedding(item["text"])
            if vector:
                self.vector_store.append({
                    "vector": vector,
                    "metadata": item["metadata"],
                    "text": item["text"]
                })
        self._initialized = True
        logging.info(f"Router initialized with {len(self.vector_store)} sites.")

    def route_query(self, user_query: str, n_results: int = 2) -> List[str]:
        """
        Find relevant site_ids for the query.
        """
        if not self._initialized:
            self.initialize_store()
            
        if not self.vector_store:
            # Fallback if routing unavailable: Return first available site
            if settings.site_registry:
                return [list(settings.site_registry.keys())[0]]
            return []

        query_vector = self._get_embedding(user_query)
        if query_vector is None:
             # Fallback on API error: Return first available site
             if settings.site_registry:
                 return [list(settings.site_registry.keys())[0]]
             return []

        # Calculate scores
        scored_results = []
        for item in self.vector_store:
            score = np.dot(query_vector, item["vector"]) / (np.linalg.norm(query_vector) * np.linalg.norm(item["vector"]))
            scored_results.append({
                "score": score,
                "site_id": item["metadata"]["site_id"]
            })
        
        # Sort by score
        scored_results.sort(key=lambda x: x["score"], reverse=True)
        
        # Filter > 0.3
        final_sites = [r["site_id"] for r in scored_results if r["score"] > 0.3][:n_results]
        
        if not final_sites:
            logging.info(f"No relevant sites found (>0.3). Top match: {scored_results[0]['site_id']} ({scored_results[0]['score']:.2f})")
            return [] 
            
        logging.info(f"Routed '{user_query}' to: {final_sites}")
        return final_sites

# Global instance
router = HubRouter()
