# Local Testing Guide

## How to Test Your RAG System Locally

Before deploying to EC2, test everything on your local computer.

---

## Step 1: Setup SSH Tunnel to Vector DB

Your vector DB is on EC2, so first create a tunnel:

```bash
# Open a terminal and run this (keep it open)
ssh -i /path/to/your-key.pem -L 8000:127.0.0.1:8000 ec2-user@54.87.100.227

# This forwards EC2's port 8000 to your local port 8000
# Keep this terminal open while testing!
```

 **What this does** : Makes the EC2 vector DB accessible at `http://localhost:8000` on your computer.

---

## Step 2: Test Vector DB Connection

Open a **new terminal** (keep SSH tunnel running) and test:

```bash
# Test 1: Health check
curl http://localhost:8000/health

# Test 2: Sample query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "diabetes symptoms",
    "privacy_level": "moderate",
    "n_results": 3
  }'
```

 **Expected** : Should return JSON with health status or search results.

 **If it fails** :

* Is SSH tunnel running? Check first terminal.
* Is vector DB running on EC2? SSH to EC2 and check: `ps aux | grep python`

---

## Step 3: Install Dependencies

```bash
# Navigate to your RAG code directory
cd /path/to/your/Confidential-Computing-RAG

# Install dependencies
pip install -r requirements.txt

# Or if you don't have requirements.txt yet:
pip install openai google-generativeai python-dotenv requests scikit-learn numpy fastapi uvicorn pydantic
```

---

## Step 4: Configure .env File

Make sure your `.env` file has:

```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-proj-YOUR_ACTUAL_KEY_HERE
VECTOR_DB_API_URL=http://127.0.0.1:8000
SITE_ID=local_test
ENCLAVE_MODE=false
ENABLE_POLICY_VERIFICATION=false
```

---

## Step 5: Test Individual Components

### Test 1: Vector DB Client

```bash
python3 -c "
from vector_db_client import VectorDBClient

client = VectorDBClient()

# Health check
if client.health_check():
    print('Vector DB is accessible')
else:
    print('Vector DB connection failed')

# Test query
results = client.query('diabetes', 'moderate', 3)
if results:
    print(f'Retrieved {len(results)} documents')
    print(f'First result: {results[0][\"content\"][:100]}...')
else:
    print('Query failed')
"
```

 **Expected output** :

```
Vector DB is accessible
Retrieved 3 documents
First result: [some medical text about diabetes]...
```

---

### Test 2: OpenAI Connection

```bash
python3 -c "
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

response = client.chat.completions.create(
    model='gpt-4o-mini',
    messages=[{'role': 'user', 'content': 'Say hello'}],
    max_tokens=10
)

print('OpenAI connection successful!')
print(f'Response: {response.choices[0].message.content}')
"
```

 **Expected output** :

```
OpenAI connection successful!
Response: Hello! How can I assist you today?
```

---

### Test 3: PHI Scrubber

```bash
python3 -c "
from phi_scrubber import PHIScrubber

scrubber = PHIScrubber()

# Test PHI scrubbing
text = 'Patient John Doe, SSN 123-45-6789, called at 555-1234'
scrubbed = scrubber.scrub(text)

print('Original:', text)
print('Scrubbed:', scrubbed)

if '[REDACTED]' in scrubbed:
    print('PHI scrubbing works')
else:
    print('PHI scrubbing failed')
"
```

 **Expected output** :

```
Original: Patient John Doe, SSN 123-45-6789, called at 555-1234
Scrubbed: Patient [REDACTED], SSN [REDACTED], called at [REDACTED]
PHI scrubbing works
```

---

### Test 4: Safety Guard

```bash
python3 -c "
from safety_guard import SafetyGuard

guard = SafetyGuard()

# Test 1: Emergency detection
is_safe, msg = guard.check_prompt('I am having chest pain', [])
print(f'Emergency test: safe={is_safe}')
if not is_safe and '911' in msg:
    print('Emergency detection works')

# Test 2: Safe query
is_safe, msg = guard.check_prompt('What are symptoms of flu?', [])
if is_safe:
    print('Safe query passes')
"
```

 **Expected output** :

```
Emergency test: safe=False
Emergency detection works
Safe query passes
```

---

## Step 6: Test Full RAG Pipeline

### Test CLI Chatbot (Interactive)

```bash
python main.py --provider openai --role staff --privacy-level low
```

 **Try these test queries** :

```
You: What are the symptoms of diabetes?
Bot: [Should return information from vector DB]

You: How is hypertension treated?
Bot: [Should return treatment information]

You: I'm having chest pain
Bot: [Should give emergency response - call 911]

You: quit
```

 **What to check** :

* Bot responds (not errors)
* Responses are relevant to query
* Emergency queries trigger safety responses
* No PHI/PII in responses
* Responses cite "medical records" or "healthcare data"

---

### Test CLI with Different Settings

```bash
# Test as student (restricted access)
python main.py --role student --privacy-level high

# Test as PI (full access)
python main.py --role pi --privacy-level none

# Test with Gemini (if you have key)
python main.py --provider gemini --role staff
```

---

## Step 7: Test API Gateway

### Start the API

Open a new terminal:

```bash
python api_gateway.py
```

 **Expected output** :

```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8080
INFO:     Application startup complete
```

Keep this running, and open **another terminal** for testing.

---

### Test API Endpoints

```bash
# Test 1: Health check
curl http://localhost:8080/health

# Expected: {"status":"healthy","site_id":"local_test",...}
```

```bash
# Test 2: Root endpoint
curl http://localhost:8080/

# Expected: {"service":"Privacy-Preserving Healthcare RAG Site Gateway",...}
```

```bash
# Test 3: Query endpoint
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What causes diabetes?",
    "role": "staff",
    "privacy_level": "low",
    "user_id": "test_user_001"
  }'

# Expected: JSON with "response", "metadata", "status"
```

```bash
# Test 4: Retrieve-only endpoint
curl -X POST http://localhost:8080/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "query": "hypertension treatment",
    "role": "pi",
    "privacy_level": "none"
  }'

# Expected: JSON with "documents" array
```

---

## Step 8: Test Different Scenarios

### Scenario 1: Emergency Query

```bash
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "I am having severe chest pain and trouble breathing",
    "role": "staff",
    "privacy_level": "low"
  }'

# Expected: Response should mention calling 911/999
```

---

### Scenario 2: Diagnosis Request (Should Block)

```bash
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Do I have diabetes? I have all the symptoms",
    "role": "student",
    "privacy_level": "high"
  }'

# Expected: Response should refuse to diagnose, suggest seeing doctor
```

---

### Scenario 3: Medication Dosage (Should Block)

```bash
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How much ibuprofen should I take for my headache?",
    "role": "staff",
    "privacy_level": "moderate"
  }'

# Expected: Response should refuse dosage, suggest consulting pharmacist
```

---

### Scenario 4: Different Privacy Levels

```bash
# High privacy (student)
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "common cold symptoms",
    "role": "student",
    "privacy_level": "high"
  }'

# Low privacy (staff)
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "common cold symptoms",
    "role": "staff",
    "privacy_level": "low"
  }'

# Compare responses - low privacy should have more detail
```

---

## Step 9: Check Logs

```bash
# View chatbot logs
tail -f logs/chatbot.log

# View audit logs
tail -f logs/query_audit.log

# View flagged prompts (safety violations)
cat logs/flagged_prompts.csv
```

---

## Success Checklist

Your system is working if:

* [ ] SSH tunnel to vector DB is active
* [ ] Vector DB health check passes
* [ ] OpenAI API connection works
* [ ] PHI scrubber removes sensitive info
* [ ] Safety guard detects emergencies
* [ ] CLI chatbot responds to queries
* [ ] API gateway starts without errors
* [ ] `/health` endpoint returns healthy status
* [ ] `/query` endpoint returns relevant responses
* [ ] Emergency queries trigger safety responses
* [ ] Diagnosis/dosage requests are blocked
* [ ] Different privacy levels work
* [ ] Logs are being created

---

## Common Issues & Fixes

### Issue: "Connection refused" to vector DB

```bash
# Fix: Check SSH tunnel is running
ps aux | grep ssh | grep 8000

# Restart tunnel if needed
ssh -i /path/to/key.pem -L 8000:127.0.0.1:8000 ec2-user@54.87.100.227
```

---

### Issue: "Invalid API key" from OpenAI

```bash
# Fix: Check .env file
cat .env | grep OPENAI_API_KEY

# Verify key is correct (should start with sk-proj-)
# Update if needed
nano .env
```

---

### Issue: "Module not found"

```bash
# Fix: Install missing dependencies
pip install -r requirements.txt

# Or install specific module
pip install openai
```

---

### Issue: API returns "Vector DB query failed"

```bash
# Fix: Check vector DB is running on EC2
ssh -i /path/to/key.pem ec2-user@54.87.100.227
ps aux | grep python

# Check logs
tail -f /path/to/vector-db/logs
```

---

### Issue: Responses don't contain relevant info

```bash
# Check what vector DB is returning
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "your test query",
    "privacy_level": "moderate",
    "n_results": 3
  }' | jq

# If results are empty, vector DB might need data
```

---

## Quick Test Script

Save this as `test_all.sh`:

```bash
#!/bin/bash

echo "🧪 Testing Healthcare RAG System"
echo "================================"

echo -e "\n1. Testing Vector DB..."
curl -s http://localhost:8000/health && echo "Vector DB accessible" || echo " Vector DB failed"

echo -e "\n2. Testing OpenAI..."
python3 -c "from openai import OpenAI; import os; from dotenv import load_dotenv; load_dotenv(); OpenAI(api_key=os.getenv('OPENAI_API_KEY')).chat.completions.create(model='gpt-4o-mini', messages=[{'role':'user','content':'hi'}], max_tokens=5); print(' OpenAI works')" 2>/dev/null || echo " OpenAI failed"

echo -e "\n3. Testing PHI Scrubber..."
python3 -c "from phi_scrubber import PHIScrubber; s = PHIScrubber(); r = s.scrub('SSN 123-45-6789'); print(' PHI scrubber works' if '[REDACTED]' in r else ' Failed')"

echo -e "\n4. Testing Safety Guard..."
python3 -c "from safety_guard import SafetyGuard; g = SafetyGuard(); safe, _ = g.check_prompt('chest pain', []); print(' Safety guard works' if not safe else ' Failed')"

echo -e "\n5. Testing API Gateway..."
curl -s http://localhost:8080/health && echo " API Gateway running" || echo " API Gateway not running"

echo -e "\n5. Testing complete!"
```

Run it:

```bash
chmod +x test_all.sh
./test_all.sh
```

---

## Performance Testing

Test response times:

```bash
# Time a single query
time curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"query": "diabetes symptoms", "role": "staff", "privacy_level": "low"}'

# Should be < 3 seconds typically
```

---

## Ready for Deployment?

Once all tests pass locally:

1. All components work individually
2. CLI chatbot works
3. API gateway works
4. Safety guards trigger correctly
5. Privacy levels work
6. Logs are generated

**You're ready to deploy to EC2!** Follow the `DEPLOYMENT_GUIDE.md`.

---

## Pro Tips

1. **Keep SSH tunnel open** - It needs to run during all local tests
2. **Test edge cases** - Try unsafe queries to ensure safety guards work
3. **Check logs** - Always review logs after testing
4. **Test both providers** - Try both OpenAI and Gemini if you have both keys
5. **Document issues** - Note any errors for troubleshooting

---

Happy testing!
