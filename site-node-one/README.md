# Confidential-Computing-Site-RAG

## Privacy-Preserving Distributed RAG System

This is a site-level implementation of a privacy-preserving RAG system for sensitive domains like healthcare. The system runs locally at each site with its own vector database and small LLM, communicating with a central hub only through anonymized, DP-protected answers.

## Architecture Overview

Each site runs:

* **Vector Database** : Local knowledge base with differential privacy controls
* **Small LLM + RAG** : Local reasoning with guardrails
* **PHI/PII Scrubbing** : HIPAA-compliant text sanitization
* **Policy Enforcement** : Role-based access control (RBAC) to KB levels
* **API Gateway** : Exposes endpoints for hub communication

The central hub never sees raw data—only aggregated, anonymized responses.

## Setup Instructions

This folder now contains everything: the FastAPI server, CLI, and the local Chroma database artifacts under `data/`. No separate `rag_data` or second server is required.

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file with your configuration:

```env
# LLM Provider Configuration
LLM_PROVIDER=openai

# API Keys
GOOGLE_API_KEY=your_api_key_here
OPENAI_API_KEY=your_api_key_here

# Vector Database (local Chroma, no separate server needed)
VECTOR_DB_MODE=local
CHROMA_DB_PATH=./data/chromadb_site1_db
CHROMA_SITE_NAME=site1
# Optional HTTP fallback:
# VECTOR_DB_MODE=http
# VECTOR_DB_API_URL=http://127.0.0.1:8000

# Site Configuration
SITE_ID=site_1
ENCLAVE_MODE=false

# Policy Verification (set to true in production)
ENABLE_POLICY_VERIFICATION=false

# Path to policy token public key (only needed if verification enabled)
POLICY_TOKEN_PUBLIC_KEY_PATH=./keys/policy_public_key.pem
```

### 3. Point to the local Chroma database

The chatbot reads the persisted Chroma DB directly (no extra FastAPI server).
The default path is `./data/chromadb_site1_db` relative to this folder; override via `CHROMA_DB_PATH` if needed.

If you still want to call a remote vector DB service instead, set `VECTOR_DB_MODE=http` and `VECTOR_DB_API_URL`.

## Usage

### Command Line Interface

Run the chatbot from the command line:

```bash
# Default settings (student role, moderate privacy)
python main.py

# Specify role and privacy level
python main.py --role pi --privacy-level low --user-id researcher_001

# Available roles: pi, admin, researcher, clinician, analyst, auditor, student, intern
# Available privacy levels: none, low, moderate, high (defaults to role's assigned level if not specified)
```

### API (for Hub Communication)

Start the API:

```bash
python server.py
```

Or use uvicorn:

```bash
uvicorn server:app --host 0.0.0.0 --port 8080
```

The gateway exposes:

* `GET /health` - Health check
* `POST /query` - Process query with full RAG pipeline
* `POST /retrieve` - Retrieval-only (no generation)

### Example API Request

```bash
curl -X 'POST' \
  'http://localhost:8080/query' \
  -H 'Content-Type: application/json' \
  -d '{
  "query": "How can I manage anxiety?",
  "role": "student",
  "privacy_level": "high",
  "user_id": "user_123"
}'
```

## Privacy & Security Features

### 1. Differential Privacy

* Vector database applies noise based on privacy level
* Privacy levels: `none`, `low`, `moderate`, `high`
* Higher levels = more noise, more anonymization

### 2. Role-Based Access Control (RBAC)

* **Student / Intern** : Access to KB1 only (High Privacy)
* **Analyst / Auditor** : KB1-KB2 (Moderate Privacy)
* **Researcher / Clinician** : KB1-KB3 (Low Privacy)
* **PI / Admin** : KB1-KB4 (None/Full Access)

### 3. PHI/PII Scrubbing

* Automatic removal of:
  * Names, emails, phone numbers
  * SSN, MRN, medical record numbers
  * Dates, addresses, ZIP codes
  * Ages over 89 (HIPAA requirement)
* Validation of LLM outputs

### 4. Safety Guardrails

* Self-harm detection and crisis response
* Prompt injection prevention
* Data exfiltration blocking
* History-based escalation detection

### 5. Policy Token Verification

In production with `ENABLE_POLICY_VERIFICATION=true`:

* Cryptographic signature verification
* Attestation from central hub
* Role and KB access validation

## File Structure

```
.
├── server.py                # FastAPI app for hub communication
├── main.py                  # CLI entry point
├── config.py                # Configuration and constants
├── chatbot.py               # Main chatbot class with policy support
├── rag_responder.py         # RAG pipeline with vector DB integration
├── safety_guard.py          # Safety checks and guardrails
├── vector_db_client.py      # Vector database client (local Chroma or HTTP fallback)
├── phi_scrubber.py          # PHI/PII scrubbing
├── policy_token.py          # Policy token handling and verification
├── data/
│   ├── build_chromadb.py    # Script to build the Chroma DB
│   └── chromadb_site1_db/   # Persisted Chroma database
├── logs/                    # Chatbot, audit, and query logs
├── requirements.txt         # Python dependencies
├── LOCAL_testing.md         # Local testing guide
└── README.md                # This file
```

## Knowledge Base Structure

The vector database (created with `all-MiniLM-L6-v2` embeddings) contains therapeutic conversation examples with metadata:

* `content`: The text chunk
* `kb_level`: KB1, KB2, KB3, or KB4 (anonymization level)
* `emotional_tone`: Detected emotional tone
* `topic_keywords`: Relevant topics
* `speaker`: Role (e.g., "Therapist", "Patient")
* `session_id`: Session identifier

## Logging & Compliance

### Query Audit Log

All queries are logged with:

* Timestamp
* Site ID
* User ID and role
* Privacy level
* Query and response lengths

Location: `./logs/query_audit.log`

### Flagged Prompts

Unsafe prompts are logged separately:

* Contains full prompt and response
* Includes policy token information
* Used for safety monitoring

Location: `./logs/flagged_prompts.csv`

## Testing

### Test Safety Guards

```python
from safety_guard import SafetyGuard

guard = SafetyGuard()

# Should be flagged
is_safe, msg = guard.check_prompt("I want to harm myself", [])
print(is_safe, msg)  # False, crisis response

# Should be safe
is_safe, msg = guard.check_prompt("I'm feeling anxious", [])
print(is_safe, msg)  # True, None
```

### Test PHI Scrubbing

```python
from phi_scrubber import PHIScrubber

scrubber = PHIScrubber()

text = "Patient John Doe, SSN 123-45-6789, called at 555-1234"
scrubbed = scrubber.scrub(text)
print(scrubbed)  # Patient [REDACTED], SSN [REDACTED], called at [REDACTED]
```

### Test Vector DB Connection

```python
from vector_db_client import VectorDBClient

client = VectorDBClient()

# Health check
if client.health_check():
    print("Vector DB is healthy")

# Query
results = client.query("anxiety", "moderate", 3)
print(f"Retrieved {len(results)} documents")
```

## Deployment Considerations

### For Confidential Computing (Enclave Mode)

1. Set `ENCLAVE_MODE=true` in config
2. Deploy inside AWS Nitro
3. Enable policy token verification
4. Configure attestation endpoint
5. Use encrypted communication channels

### Multi-Site Deployment

Each site runs independently:

* Site 1: Research Lab 1 (KB1-KB4 for local researchers)
* Site 2: Research Lab 2 (KB1-KB4 for local researchers)
* Site 3: Research Lab 3 (KB1-KB4 for local researchers)

Central hub orchestrates queries:

1. Receives user query with role/privacy level
2. Generates policy token with signature
3. Routes to relevant sites
4. Aggregates anonymized responses
5. Returns final answer

## Troubleshooting

### Vector DB Connection Issues

```bash
# Check if vector DB is running
curl http://localhost:8000/health

# Check SSH tunnel
ps aux | grep ssh

# Restart tunnel
ssh -i /path/to/key.pem -L 8000:127.0.0.1:8000 ec2-user@YOUR_IP
```

### LLM Generation Errors

* Verify `GOOGLE_API_KEY` is set correctly
* Check API quota limits
* Review logs in `./logs/chatbot.log`

### PHI in Outputs

If PHI is detected in outputs:

1. Check PHI scrubber configuration
2. Review prompt engineering in `rag_responder.py`
3. Adjust LLM temperature (lower = more deterministic)
4. Enable stricter validation

## License

This is a prototype for research and educational purposes. Please ensure compliance with HIPAA, GDPR, and other applicable regulations before deploying in production.
