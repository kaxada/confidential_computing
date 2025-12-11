import httpx
import asyncio
import logging
from app.core.config import settings

class SiteManager:
    """
    Executes queries against specific targeted sites.
    """
    def __init__(self):
        self.registry = settings.site_registry
        self.client = httpx.AsyncClient(timeout=45.0)

    async def execute_targeted_queries(self, target_site_ids: list, query: str, policy_token: dict):
        """
        Sends the query only to the sites identified by the Router.
        """
        tasks = []
        unique_ids = set(target_site_ids)
        for site_id in unique_ids:
            if site_id in self.registry:
                url = self.registry[site_id]["url"]
                tasks.append(self._query_site(site_id, url, query, policy_token))
            else:
                logging.warning(f"Target site {site_id} not found in registry.")
        
        if not tasks:
            return []

        # Wait for selected sites to respond
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed_results = []
        for res in results:
            if isinstance(res, Exception):
                logging.error(f"Task failed: {res}")
                continue
            processed_results.append(res)
            
        return processed_results

    async def _query_site(self, site_id: str, url: str, query: str, policy_token: dict):
        payload = {
            "query": query,
            "user_id": str(policy_token.get("user_id")),
            "role": policy_token.get("role"),
            "privacy_level": policy_token.get("privacy_level"),
            "site_id": settings.site_id, 
        }
        try:
            logging.info(f"Sending query to {site_id} ({url})...")
            response = await self.client.post(f"{url}/query", json=payload)
            response.raise_for_status()
            
            data = response.json()
            return {
                "site_id": site_id,
                "status": "success",
                "request_url": f"{url}/query",
                "request_payload": payload,
                "response": data.get("response"),
                "metadata": data.get("metadata")
            }
        except Exception as e:
            logging.error(f"Error querying {site_id}: {e}")
            return {
                "site_id": site_id,
                "status": "error",
                "request_url": f"{url}/query",
                "request_payload": payload,
                "error": str(e)
            }

site_manager = SiteManager()
