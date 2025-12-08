# site_manager.py
import httpx
import asyncio
import logging
import config_hub

class SiteManager:
    """
    Executes queries against specific targeted sites.
    """
    def __init__(self):
        self.registry = config_hub.SITE_REGISTRY
        self.client = httpx.AsyncClient(timeout=30.0)

    async def execute_targeted_queries(self, target_site_ids: list, query: str, policy_token: dict):
        """
        Sends the query only to the sites identified by the Router.
        """
        tasks = []
        for site_id in target_site_ids:
            if site_id in self.registry:
                url = self.registry[site_id]["url"]
                tasks.append(self._query_site(site_id, url, query, policy_token))
        
        if not tasks:
            return []

        # Wait for selected sites to respond
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results

    async def _query_site(self, site_id: str, url: str, query: str, policy_token: dict):
        try:
            payload = {
                "query": query,
                "policy_token": policy_token,
                "user_id": policy_token["user_id"],
                "role": policy_token["role"],
                "privacy_level": policy_token["privacy_level"]
            }
            
            logging.info(f"Sending query to {site_id} ({url})...")
            response = await self.client.post(f"{url}/query", json=payload)
            response.raise_for_status()
            
            data = response.json()
            return {
                "site_id": site_id,
                "status": "success",
                "response": data.get("response"),
                "metadata": data.get("metadata")
            }
        except Exception as e:
            logging.error(f"Error querying {site_id}: {e}")
            return {
                "site_id": site_id,
                "status": "error",
                "error": str(e)
            }