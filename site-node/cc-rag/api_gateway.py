# api_gateway.py
# Site gateway that exposes retrieval/answer endpoints for the central hub
# This would run inside the confidential computing enclave

from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional, List
import logging
import config
from chatbot import Chatbot
from policy_token import PolicyToken, PolicyTokenVerifier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(
    title=f"Site Gateway - {config.SITE_ID}",
    description="Privacy-preserving RAG endpoint for distributed healthcare information system",
    version="1.0.0"
)

# Initialize chatbot (shared across requests)
chatbot = Chatbot()
policy_verifier = PolicyTokenVerifier()

# --- Request/Response Models ---

class QueryRequest(BaseModel):
    """Request model for query endpoint."""
    query: str
    user_id: Optional[str] = "anonymous"
    role: Optional[str] = config.DEFAULT_ROLE
    privacy_level: Optional[str] = config.DEFAULT_PRIVACY_LEVEL
    allowed_kb_levels: Optional[List[str]] = None
    epsilon: Optional[float] = 1.0
    site_id: Optional[str] = config.SITE_ID
    timestamp: Optional[str] = ""
    signature: Optional[str] = None

class QueryResponse(BaseModel):
    """Response model for query endpoint."""
    site_id: str
    response: str
    metadata: dict
    status: str

class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    site_id: str
    enclave_mode: bool
    vector_db_healthy: bool

# --- Dependency for Policy Token Verification ---

async def verify_policy_token(
    authorization: Optional[str] = Header(None)
) -> PolicyToken:
    """
    Verifies the policy token from the request header.
    In production, this would verify the cryptographic signature.
    
    Args:
        authorization: Authorization header containing the policy token
        
    Returns:
        Verified PolicyToken
        
    Raises:
        HTTPException if token is invalid
    """
    if not config.ENABLE_POLICY_VERIFICATION:
        # In testing mode, return a default token
        return PolicyToken(
            user_id="test_user",
            role=config.DEFAULT_ROLE,
            allowed_kb_levels=config.ROLE_KB_ACCESS[config.DEFAULT_ROLE],
            privacy_level=config.DEFAULT_PRIVACY_LEVEL,
            epsilon=1.0,
            site_id=config.SITE_ID,
            timestamp="",
            signature=None
        )
    
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    # In production, parse and verify the JWT/signed token here
    # For now, we'll accept it as-is
    
    try:
        # Parse token (simplified - in production use proper JWT parsing)
        import json
        token_data = json.loads(authorization.replace("Bearer ", ""))
        token = PolicyToken.from_dict(token_data)
        
        # Verify token
        is_valid, error_msg = policy_verifier.verify_token(token)
        if not is_valid:
            raise HTTPException(status_code=403, detail=f"Invalid token: {error_msg}")
        
        return token
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token verification failed: {str(e)}")

# --- API Endpoints ---

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint to verify the site gateway is operational.
    """
    vector_db_healthy = chatbot.responder.vector_db.health_check()
    
    return HealthResponse(
        status="healthy" if vector_db_healthy else "degraded",
        site_id=config.SITE_ID,
        enclave_mode=config.ENCLAVE_MODE,
        vector_db_healthy=vector_db_healthy
    )

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Main endpoint for processing queries from the central hub.
    
    This endpoint:
    1. Receives a query with policy token
    2. Verifies the policy token
    3. Routes to appropriate KB levels based on role
    4. Returns anonymized, DP-protected response
    
    Args:
        request: QueryRequest containing query and policy information
        
    Returns:
        QueryResponse with anonymized answer
    """
    try:
        # Extract or create policy token from request
        token = policy_verifier.extract_token_from_request(request.dict())
        
        if token is None:
            raise HTTPException(
                status_code=400, 
                detail="Invalid or missing policy token information"
            )
        
        # Verify token
        is_valid, error_msg = policy_verifier.verify_token(token)
        if not is_valid and config.ENABLE_POLICY_VERIFICATION:
            raise HTTPException(status_code=403, detail=f"Token verification failed: {error_msg}")
        
        # Log the query (for audit trail)
        logging.info(
            f"Query received: user={token.user_id}, role={token.role}, "
            f"privacy={token.privacy_level}, query_len={len(request.query)}"
        )
        
        # Process query through chatbot with policy token
        response_dict = chatbot.get_response_dict(request.query, token)
        
        return QueryResponse(
            site_id=config.SITE_ID,
            response=response_dict["response"],
            metadata=response_dict["metadata"],
            status=response_dict["status"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@app.post("/retrieve")
async def retrieve_only(request: QueryRequest):
    """
    Endpoint for retrieval-only (no LLM generation).
    Returns the raw retrieved documents for the hub to aggregate.
    
    This is useful for the hub to collect context from multiple sites
    before doing centralized generation.
    """
    try:
        # Extract policy token
        token = policy_verifier.extract_token_from_request(request.dict())
        
        if token is None:
            raise HTTPException(status_code=400, detail="Invalid policy token")
        
        # Verify token
        is_valid, error_msg = policy_verifier.verify_token(token)
        if not is_valid and config.ENABLE_POLICY_VERIFICATION:
            raise HTTPException(status_code=403, detail=f"Token verification failed: {error_msg}")
        
        # Retrieve documents
        docs = chatbot.responder.retrieve(request.query, token)
        
        # Format for response
        formatted_docs = []
        for doc in docs:
            formatted_docs.append({
                "content": doc.get("content", ""),
                "metadata": {
                    "kb_level": doc.get("kb_level", "KB1"),
                    "emotional_tone": doc.get("emotional_tone"),
                    "topic_keywords": doc.get("topic_keywords", [])
                },
                "distance": doc.get("distance")
            })
        
        return {
            "site_id": config.SITE_ID,
            "documents": formatted_docs,
            "count": len(formatted_docs),
            "privacy_level": token.privacy_level
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error in retrieval: {e}")
        raise HTTPException(status_code=500, detail=f"Retrieval error: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint with basic info."""
    return {
        "service": "Privacy-Preserving Healthcare RAG Site Gateway",
        "site_id": config.SITE_ID,
        "enclave_mode": config.ENCLAVE_MODE,
        "version": "1.0.0"
    }

# For running with uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")