# vector_db_client.py
# Client for interacting with the vector database API

import logging
import os
import subprocess
import sys
from typing import Dict, List, Optional

import requests

import config

try:
    from chromadb import PersistentClient
    from chromadb.utils import embedding_functions
except Exception:
    # Defer import errors until we try to use local mode
    PersistentClient = None
    embedding_functions = None

class VectorDBClient:
    """
    Client for querying the vector database API.
    Handles communication with the local vector store running on the site.
    """
    
    def __init__(self, api_url: str = None):
        """
        Initialize the vector database client.
        
        Args:
            api_url: Base URL for the vector database API (HTTP mode only)
        """
        self.mode = config.VECTOR_DB_MODE
        self.api_url = api_url or config.VECTOR_DB_API_URL
        self.query_endpoint = config.VECTOR_DB_QUERY_ENDPOINT

        # Local Chroma configuration
        self.chroma_client = None
        self.chroma_collection_template = config.CHROMA_COLLECTION_TEMPLATE
        self.chroma_site_name = config.CHROMA_SITE_NAME
        self.chroma_db_path = config.CHROMA_DB_PATH
        self.embedding_model_name = config.DEFAULT_EMBEDDING_MODEL
        self.embedding_fn = None

        if self.mode == "local":
            self._maybe_bootstrap_chroma()
            self._init_local_chroma()
            logging.info(f"Initialized VectorDBClient in local mode with DB at {self.chroma_db_path}")
        else:
            logging.info(f"Initialized VectorDBClient in HTTP mode with endpoint: {self.query_endpoint}")

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
        
        if self.mode == "local":
            return self._query_local(query_text, privacy_level, n_results)
        return self._query_http(query_text, privacy_level, n_results)

    def health_check(self) -> bool:
        """
        Check if the vector database API is accessible.
        
        Returns:
            True if API is healthy, False otherwise
        """
        if self.mode == "local":
            return self._health_check_local()
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
    # The vector DB returns documents with 'text', 'metadata', and 'distance'
    # We need to extract and format these for the RAG pipeline
    
        formatted = {
            'content': doc.get('text', doc.get('content', doc.get('document', ''))),  # Try multiple keys
            'metadata': doc.get('metadata', {}),
            'distance': doc.get('distance', None),
            'id': doc.get('id', doc.get('metadata', {}).get('patient_id'))
        }
        
        # Extract metadata fields for easier access
        metadata = formatted['metadata']
        formatted['speaker'] = metadata.get('speaker')
        formatted['emotional_tone'] = metadata.get('emotional_tone')
        formatted['topic_keywords'] = metadata.get('topic_keywords', [])
        formatted['session_id'] = metadata.get('session_id')
        formatted['kb_level'] = metadata.get('kb_level', 'KB1')
        formatted['diagnosis_code'] = metadata.get('diagnosis_code')  # Added for healthcare
        formatted['chunk_type'] = metadata.get('chunk_type')  # Added for healthcare
        formatted['patient_id'] = metadata.get('patient_id')  # Added for healthcare
        
        return formatted

    # --- Internal helpers ---

    def _maybe_bootstrap_chroma(self):
        """Ensure the local Chroma DB exists; build if missing."""
        sqlite_path = os.path.join(self.chroma_db_path, "chroma.sqlite3")
        if os.path.exists(sqlite_path) and os.path.getsize(sqlite_path) > 0:
            return

        script_path = os.path.join(config.BASE_DIR, "data", "build_chromadb.py")
        if not os.path.exists(script_path):
            logging.warning(f"Chroma DB missing at {sqlite_path} and build script not found.")
            return

        logging.info(f"Chroma DB missing at {sqlite_path}; running build script.")
        try:
            subprocess.check_call([sys.executable, script_path], cwd=os.path.dirname(script_path))
        except Exception as e:
            logging.error(f"Failed to build Chroma DB via {script_path}: {e}")

    def _init_local_chroma(self):
        """Initialize local ChromaDB client and embedding function."""
        if PersistentClient is None or embedding_functions is None:
            logging.error("chromadb is not installed; cannot use local mode")
            return

        try:
            self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=self.embedding_model_name
            )
        except Exception as e:
            logging.error(f"Failed to load embedding model '{self.embedding_model_name}': {e}")
            self.embedding_fn = None

        try:
            self.chroma_client = PersistentClient(path=self.chroma_db_path)
        except Exception as e:
            logging.error(f"Failed to initialize Chroma client at {self.chroma_db_path}: {e}")
            self.chroma_client = None

    def _get_collection_name(self, privacy_level: str) -> str:
        return self.chroma_collection_template.format(
            site=self.chroma_site_name,
            privacy=privacy_level
        )

    def _query_local(self, query_text: str, privacy_level: str, n_results: int) -> Optional[List[Dict]]:
        """Query local ChromaDB directly (no HTTP hop)."""
        if not self.chroma_client:
            logging.error("Chroma client not initialized; cannot query locally")
            return None

        collection_name = self._get_collection_name(privacy_level)
        try:
            collection = self.chroma_client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_fn
            )
        except Exception as e:
            logging.error(f"Could not load Chroma collection '{collection_name}': {e}")
            return None

        try:
            logging.info(f"Querying local Chroma: query='{query_text[:50]}...', privacy_level={privacy_level}, n_results={n_results}")
            res = collection.query(query_texts=[query_text], n_results=n_results)
        except Exception as e:
            logging.error(f"Local Chroma query failed: {e}")
            return None

        documents = res.get("documents", [[]])[0] if res else []
        metadatas = res.get("metadatas", [[]])[0] if res else []
        distances = res.get("distances", [[]])[0] if res else []

        results = []
        for doc, meta, dist in zip(documents, metadatas, distances):
            results.append({
                "text": doc,
                "metadata": meta or {},
                "distance": dist
            })

        logging.info(f"Retrieved {len(results)} documents from local Chroma")
        return results

    def _query_http(self, query_text: str, privacy_level: str, n_results: int) -> Optional[List[Dict]]:
        """Fallback HTTP query to external vector DB service."""
        try:
            payload = {
                "query_text": query_text,
                "privacy_level": privacy_level,
                "n_results": n_results
            }
            
            logging.info(f"Querying vector DB: query='{query_text[:50]}...', privacy_level={privacy_level}, n_results={n_results}")
            
            response = requests.post(
                self.query_endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response.raise_for_status()
            
            result_data = response.json()
            if "results" in result_data:
                results = result_data["results"]
                logging.info(f"Retrieved {len(results)} documents from vector DB")
                return results
            
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

    def _health_check_local(self) -> bool:
        """Lightweight local health check for ChromaDB."""
        if not self.chroma_client:
            return False

        try:
            collection_name = self._get_collection_name(config.DEFAULT_PRIVACY_LEVEL)
            self.chroma_client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_fn
            )
            return True
        except Exception as e:
            logging.error(f"Local Chroma health check failed: {e}")
            return False
