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

# Vector Database
VECTOR_DB_API_URL=http://127.0.0.1:8000

# Site Configuration
SITE_ID=site_1
ENCLAVE_MODE=false

# Policy Verification (set to true in production)
ENABLE_POLICY_VERIFICATION=false

# Path to policy token public key (only needed if verification enabled)
POLICY_TOKEN_PUBLIC_KEY_PATH=./keys/policy_public_key.pem
```

### 3. SSH Tunnel to Vector Database

If your vector database is on a remote server, create an SSH tunnel:

```bash
ssh -i /path/to/key.pem -L 8000:127.0.0.1:8000 ec2-user@54.87.100.227
```

The vector database will now be accessible at `http://127.0.0.1:8000`.

### 4. Test Vector Database Connection

```bash
curl -X 'POST' \
  'http://localhost:8000/query' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "query_text": "anxiety coping strategies",
  "privacy_level": "moderate",
  "n_results": 3
}'
```

## Usage

### Command Line Interface

Run the chatbot from the command line:

```bash
# Default settings (student role, moderate privacy)
python main.py

# Specify role and privacy level
python main.py --role pi --privacy-level low --user-id researcher_001

# Available roles: student, collaborator, staff, pi, researcher
# Available privacy levels: none, low, moderate, high
```

### API Gateway (for Hub Communication)

Start the API gateway:

```bash
python api_gateway.py
```

Or use uvicorn:

```bash
uvicorn api_gateway:app --host 0.0.0.0 --port 8080
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

* **Student** : Access to KB1 only (heavily anonymized)
* **Collaborator** : KB1-KB2 (some detail)
* **Staff** : KB1-KB3 (moderate detail)
* **PI/Researcher** : KB1-KB4 (full access)

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
├── config.py                 # Configuration and constants
├── chatbot.py               # Main chatbot class with policy support
├── rag_responder.py         # RAG pipeline with vector DB integration
├── safety_guard.py          # Safety checks and guardrails
├── vector_db_client.py      # Vector database API client
├── phi_scrubber.py          # PHI/PII scrubbing
├── policy_token.py          # Policy token handling and verification
├── api_gateway.py           # FastAPI gateway for hub communication
├── main.py                  # CLI entry point
├── evaluations.py           # Evaluation utilities
├── requirements.txt         # Python dependencies
└── README.md               # This file
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
