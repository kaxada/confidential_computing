# vector_db_client.py
# Client for interacting with the vector database API

import requests
import logging
from typing import List, Dict, Optional
import config

class VectorDBClient:
    """
    Client for querying the vector database API.
    Handles communication with the local vector store running on the site.
    """
    
    def __init__(self, api_url: str = None):
        """
        Initialize the vector database client.
        
        Args:
            api_url: Base URL for the vector database API
        """
        self.api_url = api_url or config.VECTOR_DB_API_URL
        self.query_endpoint = config.VECTOR_DB_QUERY_ENDPOINT
        logging.info(f"Initialized VectorDBClient with endpoint: {self.query_endpoint}")

    def query(
        self, 
        query_text: str, 
        privacy_level: str, 
        n_results: int = None
    ) -> Optional[List[Dict]]:
        """
        Query the vector database with privacy-aware retrieval.
        
        Args:
            query_text: The query string to search for
            privacy_level: Privacy level ('none', 'low', 'moderate', 'high')
            n_results: Number of results to return
            
        Returns:
            List of result documents, or None if error occurs
        """
        n_results = n_results or config.DEFAULT_TOP_K
        
        try:
            # Prepare request payload
            payload = {
                "query_text": query_text,
                "privacy_level": privacy_level,
                "n_results": n_results
            }
            
            logging.info(f"Querying vector DB: query='{query_text[:50]}...', privacy_level={privacy_level}, n_results={n_results}")
            
            # Make POST request to vector DB API
            response = requests.post(
                self.query_endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30  # 30 second timeout
            )
            
            # Check for successful response
            response.raise_for_status()
            
            # Parse response
            result_data = response.json()
            
            # Extract results
            if "results" in result_data:
                results = result_data["results"]
                logging.info(f"Retrieved {len(results)} documents from vector DB")
                return results
            else:
                logging.warning("No 'results' field in vector DB response")
                return []
                
        except requests.exceptions.Timeout:
            logging.error("Vector DB query timed out")
            return None
        except requests.exceptions.ConnectionError:
            logging.error(f"Could not connect to vector DB at {self.query_endpoint}")
            return None
        except requests.exceptions.HTTPError as e:
            logging.error(f"HTTP error from vector DB: {e}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error querying vector DB: {e}")
            return None

    def health_check(self) -> bool:
        """
        Check if the vector database API is accessible.
        
        Returns:
            True if API is healthy, False otherwise
        """
        try:
            health_endpoint = f"{self.api_url}/health"
            response = requests.get(health_endpoint, timeout=5)
            return response.status_code == 200
        except Exception as e:
            logging.error(f"Vector DB health check failed: {e}")
            return False

    def format_document(self, doc: Dict) -> Dict:
        """
        Formats a document from the vector DB into a standard format.
        
        Args:
            doc: Raw document from vector DB
            
        Returns:
            Formatted document dictionary
        """
        # The vector DB returns documents with 'content', 'metadata', and 'distance'
        # We need to extract and format these for the RAG pipeline
        
        formatted = {
            'content': doc.get('content', doc.get('document', '')),
            'metadata': doc.get('metadata', {}),
            'distance': doc.get('distance', None),
            'id': doc.get('id', None)
        }
        
        # Extract metadata fields for easier access
        metadata = formatted['metadata']
        formatted['speaker'] = metadata.get('speaker')
        formatted['emotional_tone'] = metadata.get('emotional_tone')
        formatted['topic_keywords'] = metadata.get('topic_keywords', [])
        formatted['session_id'] = metadata.get('session_id')
        formatted['kb_level'] = metadata.get('kb_level', 'KB1')
        
        return formatted