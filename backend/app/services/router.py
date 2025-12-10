from typing import List
import numpy as np
import json
import re
from openai import OpenAI
from app.core.config import settings
import logging

class HubRouter:
    """
    Intelligent Router using LLM reasoning with Vector Search Fallback.
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

    def _llm_route_query(self, user_query: str) -> List[str]:
        """
        Uses an LLM to reason about which sites to query based on descriptions.
        """
        client = self._get_client()
        if not client:
            return []

        # Construct descriptions context
        site_descriptions = ""
        for item in settings.site_metadata:
            site_id = item['metadata']['site_id']
            desc = item['text']
            site_descriptions += f"- ID: {site_id}\n  Description: {desc}\n\n"

        prompt = f"""
        You are the Routing Agent for a Confidential Computing Hub.
        Your goal is to select the most relevant data sites for the user's query.

        Available Sites:
        {site_descriptions}

        User Query: "{user_query}"

        Instructions:
        1. Analyze the query and the site descriptions.
        2. Select ALL sites that might contain relevant data.
        3. If the user explicitly asks for a site (e.g. "Site 1"), include it.
        4. If the query requires combining data (e.g. "compare demographics and lab results"), select all relevant sites.
        5. Return ONLY a valid JSON list of strings containing the site IDs.
           Example: ["site_1", "site_3"]
        """

        try:
            response = client.chat.completions.create(
                model=settings.aggregation_model, # Use the same smart model (e.g. GPT-4)
                messages=[
                    {"role": "system", "content": "You are a precise routing assistant. Output only JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0
            )
            content = response.choices[0].message.content.strip()
            
            # extract JSON if wrapped in code blocks
            match = re.search(r'\[.*\]', content, re.DOTALL)
            if match:
                json_str = match.group(0)
                site_ids = json.loads(json_str)
                # Validate
                valid_ids = [s for s in site_ids if s in settings.site_registry]
                logging.info(f"LLM Routing Decision: {valid_ids}")
                return valid_ids
            else:
                logging.warning(f"LLM Routing failed to produce JSON. Raw: {content}")
                return []
                
        except Exception as e:
            logging.error(f"LLM Routing error: {e}")
            return []

    def route_query(self, user_query: str, n_results: int = 2) -> List[str]:
        """
        Find relevant site_ids for the query.
        Prioritizes LLM reasoning, falls back to semantic/explicit search.
        """
        
        # 1. Try LLM Routing (The "Intelligent" path)
        llm_sites = self._llm_route_query(user_query)
        if llm_sites:
            return llm_sites

        # 2. Fallback: Semantic + Explicit Logic
        logging.info("Falling back to standard semantic routing.")
        
        if not self._initialized:
            self.initialize_store()
            
        # Check for explicit site mentions
        explicit_sites = set()
        lower_query = user_query.lower()
        
        site_mappings = {
            "site 1": "site_1", "site one": "site_1", "site_1": "site_1",
            "site 2": "site_2", "site two": "site_2", "site_2": "site_2",
            "site 3": "site_3", "site three": "site_3", "site_3": "site_3"
        }
        
        for key, site_id in site_mappings.items():
            if key in lower_query:
                explicit_sites.add(site_id)

        if not self.vector_store:
            if explicit_sites:
                return list(explicit_sites)
            if settings.site_registry:
                return [list(settings.site_registry.keys())[0]]
            return []

        query_vector = self._get_embedding(user_query)
        if query_vector is None:
             if explicit_sites:
                 return list(explicit_sites)
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
        
        scored_results.sort(key=lambda x: x["score"], reverse=True)
        
        semantic_sites = [r["site_id"] for r in scored_results if r["score"] > 0.25]
        
        final_sites = list(explicit_sites)
        for s in semantic_sites:
            if s not in final_sites and len(final_sites) < n_results:
                final_sites.append(s)
                
        if not final_sites:
            logging.info(f"No relevant sites found (>0.25). Top match: {scored_results[0]['site_id']} ({scored_results[0]['score']:.2f})")
            return [] 
            
        logging.info(f"Routed '{user_query}' to: {final_sites}")
        return final_sites

# Global instance
router = HubRouter()
