# Confidential-Computing-Hub/hub_router.py
import requests
import logging

class HubRouter:
    """
    New Router using Vector Search (Port 9001)
    """
    def __init__(self):
        self.metadata_db_url = "http://localhost:9001/search"

    def route_query(self, user_query: str) -> list[str]:
        """
        Queries the Metadata DB to find the best site.
        Returns a list of site_ids.
        """
        try:
            payload = {
                "query_text": user_query,
                "n_results": 2  # Get top 2 matches if needed
            }
            
            response = requests.post(self.metadata_db_url, json=payload)
            data = response.json()
            results = data.get("results", [])
            
            if not results:
                logging.warning("Router found no matching sites.")
                return []

            # Extract site_ids
            # We can also dynamically capture the URL here if we wanted to
            # update the SiteManager registry dynamically.
            target_sites = [r["site_id"] for r in results]
            
            logging.info(f"Vector Search routed '{user_query}' to: {target_sites}")
            return target_sites

        except Exception as e:
            logging.error(f"Routing DB Error: {e}")
            return []