# hub_server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
from token_issuer import TokenIssuer
from hub_router import HubRouter  # <-- New Import
from site_manager import SiteManager
from aggregator import ResultAggregator

logging.basicConfig(level=logging.INFO)
app = FastAPI(title="Confidential Computing Hub", description="Semantic Routing Enabled")

token_issuer = TokenIssuer()
hub_router = HubRouter()       # <-- Initialize Router
site_manager = SiteManager()
aggregator = ResultAggregator()

class HubRequest(BaseModel):
    query: str
    user_id: str
    role: str = "staff"
    privacy_level: str = "low"

@app.post("/hub/query")
async def hub_entry_point(request: HubRequest):
    """
    1. Validate User & Generate Token
    2. Route Query (Hub RAG -> Target Sites)
    3. Execute Queries
    4. Aggregate Results
    """
    logging.info(f"Hub Request: {request.user_id} | Query: {request.query}")

    # 1. Attestation
    token = token_issuer.generate_policy_token(
        request.user_id, request.role, request.privacy_level
    )

    # 2. Semantic Routing (The "Hub RAG" step)
    # The Hub uses its metadata to find the right site(s)
    target_sites = hub_router.route_query(request.query)
    
    if not target_sites:
        return {"hub_answer": "I couldn't find any relevant data sites for your specific query in the Hub Registry."}

    # 3. Execution (Targeted)
    results = await site_manager.execute_targeted_queries(target_sites, request.query, token)

    # 4. Insights
    final_insight = aggregator.synthesize_results(request.query, results)

    return {
        "hub_answer": final_insight,
        "routed_to": target_sites, # Debug info: shows user where the query went
        "site_responses": results
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)