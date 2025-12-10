# Confidential-Computing-RAG/populate_sites.py
import requests

VECTOR_DB_URL = "http://localhost:8000/add_documents"

SYNTHETIC_DATA = [
    # --- SITE 1 DATA (Labs) ---
    {
        "content": "Patient PAT001 Lab Report: Creatinine 1.4 mg/dL (High), BUN 25 mg/dL. Urinalysis shows trace protein. Interpretation: Early signs of renal insufficiency.",
        "metadata": {"source": "site_1", "type": "lab_report", "patient_id": "PAT001", "kb_level": "KB2"}
    },
    {
        "content": "Patient PAT002 Lab Report: HbA1c 8.2%. Glucose Fasting 160 mg/dL. Lipid Panel: LDL 140, HDL 35. Interpretation: Poorly controlled diabetes.",
        "metadata": {"source": "site_1", "type": "lab_report", "patient_id": "PAT002", "kb_level": "KB2"}
    },
    # --- SITE 2 DATA (Diagnosis) ---
    {
        "content": "Patient PAT001 Diagnosis: Chronic Kidney Disease (CKD) Stage 2 (N18.2). Plan: Monitor BP, avoid NSAIDs, refer to Nephrology.",
        "metadata": {"source": "site_2", "type": "diagnosis", "patient_id": "PAT001", "kb_level": "KB2"}
    },
    {
        "content": "Patient PAT002 Diagnosis: Type 2 Diabetes Mellitus (E11.9) with Hyperlipidemia. Rx: Metformin 1000mg BID, Atorvastatin 20mg QHS.",
        "metadata": {"source": "site_2", "type": "diagnosis", "patient_id": "PAT002", "kb_level": "KB2"}
    },
    # --- SITE 3 DATA (Demographics) ---
    {
        "content": "Patient PAT001: John Doe, DOB 1965-05-20. Insurance: BlueCross. Emergency Contact: Jane Doe (Spouse). History: Smoker (10 years, quit).",
        "metadata": {"source": "site_3", "type": "demographics", "patient_id": "PAT001", "kb_level": "KB2"}
    },
    {
        "content": "Patient PAT002: Sarah Smith, DOB 1978-11-12. Insurance: Aetna. History: No alcohol, social drinker. Family History: Mother had T2DM.",
        "metadata": {"source": "site_3", "type": "demographics", "patient_id": "PAT002", "kb_level": "KB2"}
    }
]

print("Sending data to Mock Vector DB...")
try:
    response = requests.post(VECTOR_DB_URL, json=SYNTHETIC_DATA)
    if response.status_code == 200:
        print("Success! Data ingested.")
        print(f"DB Response: {response.json()}")
    else:
        print(f"Failed: {response.text}")
except Exception as e:
    print(f"Connection Error: {e}")
    print("Make sure 'python mock_vector_db.py' is running in another terminal!")