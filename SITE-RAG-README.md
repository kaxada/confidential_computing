# Privacy-Preserving Distributed RAG System for Healthcare

A secure, privacy-aware Retrieval-Augmented Generation (RAG) system designed for sensitive healthcare domains. The system implements a distributed architecture where multiple healthcare sites (hospitals, clinics, research centers) run their own local RAG instances with privacy-preserving mechanisms including differential privacy, role-based access control, and PHI/PII scrubbing.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Multi-Site Deployment](#multi-site-deployment)
- [Usage](#usage)
- [Privacy Levels](#privacy-levels)
- [Role-Based Access Control](#role-based-access-control)
- [Safety Features](#safety-features)
- [API Reference](#api-reference)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

---

## Overview

This system enables secure querying of sensitive healthcare data across multiple sites without exposing raw patient information. Each site maintains its own vector database and RAG pipeline, returning only anonymized, differential privacy-protected responses to queries.

### Key Capabilities

- **Privacy-Preserving Retrieval**: Differential privacy (DP) noise applied at query time
- **Multi-Level Access Control**: Role-based knowledge base access (KB1-KB4)
- **PHI/PII Protection**: Automatic scrubbing of protected health information
- **Distributed Architecture**: Each site runs independently with local data
- **Flexible LLM Support**: Compatible with OpenAI GPT-4o-mini and Google Gemini
- **Healthcare Safety Guards**: Built-in detection for medical emergencies and unsafe queries
- **Audit Logging**: Complete query tracking for compliance

---

## Architecture

### System Design

The system follows a hub-and-spoke architecture where:

1. **Central Hub**: Orchestrates queries across multiple sites
2. **Site Nodes**: Independent RAG instances at each healthcare facility
3. **Vector Databases**: Local knowledge bases with varying privacy levels
4. **Policy Tokens**: Cryptographically signed access credentials

### Three-Site Deployment

The current deployment includes three specialized healthcare sites:

#### Site 1: General Medical (Primary Care)
- **Specialty**: Primary care, chronic disease management
- **Data**: Diabetes, hypertension, cholesterol screening
- **Location**: EC2 instance at 54.87.100.227
- **Vector DB Port**: 8000
- **RAG API Port**: 8080

#### Site 2: Oncology (Cancer Center)
- **Specialty**: Cancer treatment and research
- **Data**: Cancer staging, chemotherapy, tumor markers
- **Location**: EC2 instance at 98.93.26.67
- **Vector DB Port**: 8000
- **RAG API Port**: 8081

#### Site 3: Emergency Department
- **Specialty**: Acute care and emergency medicine
- **Data**: Triage, cardiac events, overdoses, respiratory distress
- **Location**: EC2 instance at 3.236.74.139
- **Vector DB Port**: 8000
- **RAG API Port**: 8082

### Data Flow

```
User Query → Policy Token Verification → Safety Guard Check → 
Vector DB Retrieval (with DP) → KB-Level Filtering → PHI Scrubbing → 
LLM Generation → Output Validation → Anonymized Response
```

---

## Features

### Privacy Protection

- **Differential Privacy**: Configurable noise levels (none, low, moderate, high)
- **Knowledge Base Levels**: Four-tier access control (KB1-KB4)
- **PHI Scrubbing**: Removes names, SSNs, addresses, phone numbers, dates
- **Output Validation**: Final check for leaked sensitive information

### Safety Mechanisms

- **Emergency Detection**: Identifies life-threatening situations
- **Self-Harm Prevention**: Crisis hotline referrals
- **Diagnosis Blocking**: Prevents medical diagnosis by AI
- **Dosage Prevention**: Blocks medication dosage recommendations
- **Alternative Medicine Warnings**: Cautions against unsafe substitutions

### Access Control

- **Role-Based Access**: Student, Collaborator, Staff, PI, Researcher
- **Privacy Levels**: None (full), Low, Moderate, High (maximum anonymization)
- **Policy Tokens**: Cryptographically signed authorization

### Audit & Compliance

- **Query Logging**: Complete audit trail with timestamps
- **Safety Violations**: Separate log for flagged prompts
- **HIPAA Compliance**: PHI protection mechanisms
- **GDPR Ready**: Data anonymization and access controls

---

## System Requirements

### Software Dependencies

- Python 3.9 or higher
- pip (Python package manager)
- Virtual environment support

### Common Required Python Packages

- openai >= 1.0.0
- google-generativeai >= 0.3.0 (optional)
- fastapi >= 0.104.0
- uvicorn >= 0.24.0
- requests >= 2.31.0
- python-dotenv >= 1.0.0
- scikit-learn >= 1.3.0
- numpy >= 1.24.0
- pydantic >= 2.0.0

### API Keys Required

- OpenAI API key (for GPT-4o-mini)
- OR Google API key (for Gemini 1.5 Flash)

---

## Installation

### Step 1: Clone or Transfer Code

For each site, create a directory and transfer the code:

```bash
# On each EC2 instance
mkdir -p ~/site-rag
cd ~/site-rag
```

From your local machine:

```bash
# Transfer files to Site 1
scp -i your-key.pem \
    config.py chatbot.py rag_responder.py safety_guard.py \
    vector_db_client.py phi_scrubber.py policy_token.py \
    api_gateway.py main.py requirements.txt \
    ec2-user@54.87.100.227:~/site-rag/

# Repeat for Site 2 and Site 3 with their respective IPs
```

### Step 2: Install Dependencies

On each EC2 instance:

```bash
cd ~/site-rag

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### Step 3: Configure Environment

Create a `.env` file with site-specific settings (see Configuration section).

### Step 4: Verify Installation

```bash
# Test vector database connection
curl http://127.0.0.1:8000/health

# Test RAG system
python main.py --role pi --privacy-level none
```

---

## Configuration

### Environment Variables

Each site requires a `.env` file with the following configuration:

#### Site 1 Configuration

```bash
# LLM Provider
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-proj-your_api_key_here

# Vector Database
VECTOR_DB_MODE=http
VECTOR_DB_API_URL=http://127.0.0.1:8000

# Site Identification
SITE_ID=site1
CHROMA_SITE_NAME=site1

# Privacy & Policy
ENCLAVE_MODE=false
ENABLE_POLICY_VERIFICATION=false
DEFAULT_PRIVACY_LEVEL=moderate

# Logging
DEFAULT_LOG_PATH=./logs/chatbot.log
DEFAULT_FLAGGED_PROMPTS_PATH=./logs/flagged_prompts.csv
```

#### Site 2 Configuration

```bash
# LLM Provider
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-proj-your_api_key_here

# Vector Database
VECTOR_DB_MODE=http
VECTOR_DB_API_URL=http://127.0.0.1:8000

# Site Identification
SITE_ID=site2
CHROMA_SITE_NAME=site2

# Privacy & Policy
ENCLAVE_MODE=false
ENABLE_POLICY_VERIFICATION=false
DEFAULT_PRIVACY_LEVEL=moderate
```

#### Site 3 Configuration

```bash
# LLM Provider
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-proj-your_api_key_here

# Vector Database
VECTOR_DB_MODE=http
VECTOR_DB_API_URL=http://127.0.0.1:8000

# Site Identification
SITE_ID=site3
CHROMA_SITE_NAME=site3

# Privacy & Policy
ENCLAVE_MODE=false
ENABLE_POLICY_VERIFICATION=false
DEFAULT_PRIVACY_LEVEL=moderate
```

### Configuration Parameters

| Parameter | Description | Options |
|-----------|-------------|---------|
| LLM_PROVIDER | Language model provider | openai, gemini |
| VECTOR_DB_MODE | Vector database access mode | http, local |
| SITE_ID | Unique site identifier | site1, site2, site3 |
| DEFAULT_PRIVACY_LEVEL | Default privacy if not specified | none, low, moderate, high |
| ENABLE_POLICY_VERIFICATION | Cryptographic token verification | true, false |
| ENCLAVE_MODE | Confidential computing mode | true, false |

---

## Multi-Site Deployment

### Deploying Site 1 (General Medical)

```bash
# SSH to Site 1
ssh -i your-key.pem ec2-user@54.87.100.227

# Create directory
mkdir -p ~/site1-rag
cd ~/site1-rag

# Transfer files (from local machine)
# Create .env with SITE_ID=site1

# Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Test
python main.py --role pi --privacy-level none
```

### Deploying Site 2 (Oncology)

```bash
# SSH to Site 2
ssh -i your-key.pem ec2-user@98.93.26.67

# Create directory
mkdir -p ~/site2-rag
cd ~/site2-rag

# Transfer files (from local machine)
# Create .env with SITE_ID=site2

# Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Test
python main.py --role pi --privacy-level none
```

### Deploying Site 3 (Emergency)

```bash
# SSH to Site 3
ssh -i your-key.pem ec2-user@3.236.74.139

# Create directory
mkdir -p ~/site3-rag
cd ~/site3-rag

# Transfer files (from local machine)
# Create .env with SITE_ID=site3

# Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Test
python main.py --role pi --privacy-level none
```

### Running API Gateways

Each site should run its API gateway on a unique port:

```bash
# Site 1
cd ~/site1-rag
source venv/bin/activate

# Site 2
cd ~/site2-rag
source venv/bin/activate

# Site 3
cd ~/site3-rag
source venv/bin/activate
```

### Running as Background Services

For production deployment, use systemd:

```bash
# Create service file
sudo nano /etc/systemd/system/site1-rag.service
```

```ini
[Unit]
Description=Site 1 RAG API Gateway
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/site1-rag
Environment="PATH=/home/ec2-user/site1-rag/venv/bin"
ExecStart=/home/ec2-user/site1-rag/venv/bin/uvicorn api_gateway:app --host 0.0.0.0 --port 8080
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable site1-rag
sudo systemctl start site1-rag
sudo systemctl status site1-rag
```

---

## Usage

### Command Line Interface

#### Basic Usage

```bash
# Activate virtual environment
source venv/bin/activate

# Run chatbot with default settings
python main.py

# Specify role and privacy level
python main.py --role pi --privacy-level none

# Use specific LLM provider
python main.py --provider openai --role staff --privacy-level low
```

#### Available Arguments

```
--role              User role (student, collaborator, staff, pi, researcher)
--privacy-level     Privacy level (none, low, moderate, high)
--provider          LLM provider (openai, gemini)
--user-id          User identifier for logging
```

#### Example Queries by Site

**Site 1 (General Medical):**
```
You: Find all diabetic patients with HbA1c over 8 who are on metformin
You: Patients with hypertension prescribed lisinopril showing elevated blood pressure
You: Patients over 50 with no recent cholesterol screening
```

**Site 2 (Oncology):**
```
You: Stage III cancer patients on pembrolizumab with elevated tumor markers
You: Breast cancer patients with CA 15-3 levels responding to chemotherapy
You: Advanced cancer patients in palliative care with pain management needs
```

**Site 3 (Emergency):**
```
You: Triage level 1 patients with cardiac symptoms and unstable vital signs
You: Overdose patients administered naloxone with positive drug screens
You: Pediatric patients under 10 with respiratory distress requiring intervention
```

### API Usage

#### Health Check

```bash
curl http://localhost:8080/health
```

Response:
```json
{
  "status": "healthy",
  "site_id": "site1",
  "enclave_mode": false,
  "vector_db_healthy": true
}
```

#### Query Endpoint

```bash
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Find patients with diabetes",
    "role": "staff",
    "privacy_level": "low",
    "user_id": "staff_001"
  }'
```

Response:
```json
{
  "site_id": "site1",
  "response": "Found multiple patients with diabetes...",
  "metadata": {
    "site_id": "site1",
    "privacy_level": "low",
    "role": "staff",
    "timestamp": "2025-12-09T22:30:00"
  },
  "status": "success"
}
```

#### Retrieve-Only Endpoint

```bash
curl -X POST http://localhost:8080/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "query": "diabetes treatment",
    "role": "pi",
    "privacy_level": "none"
  }'
```

---

## Privacy Levels

### Level Definitions

#### None (Full Access)
- **Users**: Principal Investigators, Authorized Researchers
- **PHI Scrubbing**: Disabled
- **Data Shown**: Patient IDs, diagnosis codes, full details
- **Use Case**: Research analysis, detailed patient reviews

#### Low (Minimal Privacy)
- **Users**: Healthcare staff, clinical coordinators
- **PHI Scrubbing**: Partial (removes SSN, names, dates)
- **Data Shown**: Diagnosis codes, general patient information
- **Use Case**: Clinical support, care coordination

#### Moderate (Standard Privacy)
- **Users**: External collaborators, research partners
- **PHI Scrubbing**: Full (removes all identifiers)
- **Data Shown**: Aggregated statistics, general medical information
- **Use Case**: Collaborative research, data sharing

#### High (Maximum Privacy)
- **Users**: Students, external users, public access
- **PHI Scrubbing**: Maximum (heavily anonymized)
- **Data Shown**: Very general information, educational content
- **Use Case**: Education, general information queries

### Privacy Level Comparison

| Feature | None | Low | Moderate | High |
|---------|------|-----|----------|------|
| Patient IDs | Visible | Hidden | Hidden | Hidden |
| Diagnosis Codes | Visible | Visible | Hidden | Hidden |
| Names | Visible | Hidden | Hidden | Hidden |
| Dates | Visible | Hidden | Hidden | Hidden |
| Addresses | Visible | Hidden | Hidden | Hidden |
| Phone Numbers | Visible | Hidden | Hidden | Hidden |
| DP Noise | 0% | 10% | 50% | 90% |

---

## Role-Based Access Control

### Role Hierarchy

```
Student (KB1) < Collaborator (KB1-KB2) < Staff (KB1-KB3) < PI/Researcher (KB1-KB4)
```

### Knowledge Base Levels

- **KB1**: Heavily anonymized, maximum DP noise
- **KB2**: Moderate anonymization, some identifiers removed
- **KB3**: Light anonymization, diagnosis codes visible
- **KB4**: Minimal anonymization, most details visible

### Role Permissions

| Role | KB Access | Typical Use Case |
|------|-----------|------------------|
| Student | KB1 | Educational queries, learning |
| Collaborator | KB1-KB2 | Research collaboration, data analysis |
| Staff | KB1-KB3 | Clinical support, patient care |
| PI | KB1-KB4 | Full research access, detailed analysis |
| Researcher | KB1-KB4 | Authorized research, data collection |

---

## Safety Features

### Emergency Detection

The system detects medical emergencies and provides immediate guidance:

- Chest pain, heart attack, stroke
- Difficulty breathing, respiratory distress
- Severe bleeding, head injury
- Poisoning, overdose, allergic reactions
- Unconsciousness, seizures

**Response**: Directs to call 911 (US/Canada), 999 (UK), or local emergency number.

### Self-Harm Prevention

Detects language indicating self-harm or suicidal ideation:

- "I want to harm myself"
- "Thinking about suicide"
- "Want to end my life"

**Response**: Provides crisis hotline numbers (988 in US/Canada, 111 in UK).

### Medical Advice Blocking

The system refuses to:

- Provide medical diagnoses
- Recommend medication dosages
- Suggest stopping prescribed treatments
- Replace medical care with alternative medicine

**Response**: Advises consulting qualified healthcare providers.

### Data Exfiltration Prevention

Blocks attempts to:

- Send data to external URLs
- Email patient information
- Forward records to third parties

**Response**: Warns about privacy and security policies.

---

## API Reference

### Endpoints

#### GET /health

Check system health status.

**Response:**
```json
{
  "status": "healthy",
  "site_id": "site1",
  "enclave_mode": false,
  "vector_db_healthy": true
}
```

#### POST /query

Process a healthcare query with privacy controls.

**Request Body:**
```json
{
  "query": "Find patients with diabetes",
  "role": "staff",
  "privacy_level": "low",
  "user_id": "staff_001"
}
```

**Response:**
```json
{
  "site_id": "site1",
  "response": "Found multiple patients...",
  "metadata": {
    "privacy_level": "low",
    "role": "staff",
    "timestamp": "2025-12-09T22:30:00"
  },
  "status": "success"
}
```

#### POST /retrieve

Retrieve documents without LLM generation.

**Request Body:**
```json
{
  "query": "diabetes treatment",
  "role": "pi",
  "privacy_level": "none"
}
```

**Response:**
```json
{
  "site_id": "site1",
  "documents": [
    {
      "content": "Patient information...",
      "metadata": {...},
      "distance": 0.5
    }
  ],
  "count": 3,
  "privacy_level": "none"
}
```

---

## Testing

### Unit Tests

Test individual components:

```bash
# Test vector DB connection
python3 -c "from vector_db_client import VectorDBClient; \
  c = VectorDBClient(); \
  print('Connected' if c.health_check() else 'Failed')"

# Test PHI scrubber
python3 -c "from phi_scrubber import PHIScrubber; \
  s = PHIScrubber(); \
  print(s.scrub('SSN 123-45-6789'))"

# Test safety guard
python3 -c "from safety_guard import SafetyGuard; \
  g = SafetyGuard(); \
  safe, msg = g.check_prompt('chest pain', []); \
  print('Blocked' if not safe else 'Passed')"
```

### Integration Tests

Test complete workflow:

```bash
# Test with different privacy levels
python main.py --role pi --privacy-level none
python main.py --role staff --privacy-level low
python main.py --role student --privacy-level high
```

### API Tests

```bash
# Test health endpoint
curl http://localhost:8080/health

# Test query endpoint
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"query": "diabetes", "role": "staff", "privacy_level": "low"}'
```

---

## Troubleshooting

### Common Issues

#### Vector DB Connection Failed

**Symptom**: "Vector DB connection failed" or "Collection does not exist"

**Solution**:
```bash
# Check vector DB is running
curl http://127.0.0.1:8000/health

# Verify VECTOR_DB_MODE in .env
cat .env | grep VECTOR_DB_MODE
# Should show: VECTOR_DB_MODE=http

# Check logs
tail -50 logs/chatbot.log
```

#### OpenAI API Key Invalid

**Symptom**: "Invalid API key" or authentication errors

**Solution**:
```bash
# Verify API key in .env
cat .env | grep OPENAI_API_KEY

# Test API key directly
python3 -c "from openai import OpenAI; \
  import os; from dotenv import load_dotenv; \
  load_dotenv(); \
  client = OpenAI(api_key=os.getenv('OPENAI_API_KEY')); \
  print('Valid' if client else 'Invalid')"
```

#### No Results Returned

**Symptom**: "I couldn't find specific information"

**Solution**:
```bash
# Test vector DB directly
curl -X POST http://127.0.0.1:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query_text": "diabetes", "privacy_level": "none", "n_results": 3}'

# Check if collections exist
curl http://127.0.0.1:8000/health

# Verify site configuration
python3 -c "import config; print(f'Site: {config.SITE_ID}')"
```

#### Port Already in Use

**Symptom**: "Address already in use" when starting API

**Solution**:
```bash
# Find process using port
sudo lsof -i :8080

# Kill process
sudo kill -9 <PID>

# Or use different port
uvicorn api_gateway:app --host 0.0.0.0 --port 8081
```

### Log Locations

- **Chatbot logs**: `./logs/chatbot.log`
- **Flagged prompts**: `./logs/flagged_prompts.csv`
- **Query audit**: `./logs/query_audit.log`

### Getting Help

1. Check logs: `tail -f logs/chatbot.log`
2. Verify configuration: `cat .env`
3. Test components individually
4. Review documentation for your specific site
5. Check vector DB health: `curl http://127.0.0.1:8000/health`

---

## Contributing

### Development Setup

```bash
# Clone repository
git clone <repository-url>

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

```


