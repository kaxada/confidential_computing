#!/usr/bin/env python3
"""
Improved ChromaDB Setup with Consistent PHI Handling
- Ensures ALL chunks have the same PHI structure
- Maintains consistency across queries at same privacy level
Author: Dilip Thakur
"""

import pandas as pd
import numpy as np
from chromadb import PersistentClient
from chromadb.utils import embedding_functions
import re
import os

# ---------------------------
# Differential Privacy Processor
# ---------------------------
class DifferentialPrivacyProcessor:
    def __init__(self, epsilon: float = 1.0):
        self.epsilon = epsilon
        self.sensitivity = 1.0

    def generalize_age(self, age: int, level: str = 'moderate') -> str:
        if level == 'none': 
            return str(age)
        elif level == 'low': 
            lower = (age // 5) * 5
            return f"{lower}-{lower+4}"
        elif level == 'moderate': 
            lower = (age // 10) * 10
            return f"{lower}-{lower+9}"
        else:  # high
            lower = (age // 20) * 20
            return f"{lower}-{lower+19}"

    def apply_privacy_to_patient_header(self, header: str, privacy_level: str) -> str:
        """
        Apply consistent privacy transformations to patient header
        This ensures ALL chunks have the same level of PHI redaction
        """
        if privacy_level == 'none':
            return header  # Full details
        
        elif privacy_level == 'low':
            # Partial redaction
            header = re.sub(r'SSN: \d{3}-\d{2}-(\d{4})', r'SSN: XXX-XX-\1', header)
            header = re.sub(r'(\w+)@(\w+\.\w+)', r'***@\2', header)
            # Keep name, DOB, partial phone
            
        elif privacy_level == 'moderate':
            # More redaction
            header = re.sub(r'Patient (\w)\w* (\w)\w*', r'Patient \1*** \2***', header)
            header = re.sub(r'SSN: \d{3}-\d{2}-\d{4}', 'SSN: XXX-XX-XXXX', header)
            header = re.sub(r'DOB: \d{2}/\d{2}/\d{4}', 'DOB: [REDACTED]', header)
            header = re.sub(r'\d{3}[.-]\d{3}[.-]\d{4}', 'XXX-XXX-XXXX', header)
            header = re.sub(r'\w+@\w+\.\w+', '[EMAIL_REDACTED]', header)
            
        elif privacy_level == 'high':
            # Complete redaction
            header = re.sub(r'Patient \w+ \w+', 'Patient [NAME_REDACTED]', header)
            header = re.sub(r'SSN: \d{3}-\d{2}-\d{4}', 'SSN: [REDACTED]', header)
            header = re.sub(r'DOB: \d{2}/\d{2}/\d{4}', 'DOB: [REDACTED]', header)
            header = re.sub(r'Lives at .+?\.', 'Lives at [ADDRESS_REDACTED].', header)
            header = re.sub(r'Contact: .+?\.', 'Contact: [PHONE_REDACTED].', header)
            header = re.sub(r'Email: .+?\.', 'Email: [EMAIL_REDACTED].', header)
            header = re.sub(r'Insurance: \w+\d+', 'Insurance: [REDACTED]', header)
            
        return header

# ---------------------------
# Enhanced Chunking Function
# ---------------------------
def create_patient_header(record):
    """
    Create a consistent patient header that will be prepended to ALL chunks
    This ensures every chunk has the same patient identification info
    """
    # Extract PHI from notes if available
    if 'notes' in record and pd.notna(record['notes']):
        notes = record['notes']
        # Try to extract the patient header from notes
        match = re.search(r'(Patient .+?) (?:presents|arrived)', notes)
        if match:
            return match.group(1) + ". "
    
    # Fallback: construct basic header
    header = f"Patient {record['patient_id']}"
    if 'age' in record and pd.notna(record['age']):
        header += f", Age: {record['age']}"
    if 'gender' in record and pd.notna(record['gender']):
        header += f", Gender: {record['gender']}"
    return header + ". "

def chunk_record_with_consistent_phi(record, privacy_level='none'):
    """
    Create chunks where EVERY chunk has the same patient header
    This ensures consistency across all queries
    """
    chunks = []
    pid = record['patient_id']
    
    # Create the patient header that will be used for ALL chunks
    patient_header = create_patient_header(record)
    
    # Apply privacy level to the header
    dp = DifferentialPrivacyProcessor()
    protected_header = dp.apply_privacy_to_patient_header(patient_header, privacy_level)
    
    # Apply age generalization if needed
    if 'age' in record and pd.notna(record['age']) and privacy_level != 'none':
        age_str = str(int(record['age']))
        age_range = dp.generalize_age(int(record['age']), privacy_level)
        protected_header = protected_header.replace(f"Age: {age_str}", f"Age: {age_range}")
    
    # Now create chunks, each with the same patient header
    
    # 1. Demographics + Diagnosis Chunk
    demo_content = f"Diagnosis: {record['diagnosis_description']} (ICD-10: {record['diagnosis_code']}). "
    demo_content += f"Chief complaint: {record['chief_complaint']}."
    
    demo_chunk = {
        'text': protected_header + demo_content,
        'metadata': {
            'patient_id': pid,
            'chunk_type': 'demographics',
            'diagnosis_code': record['diagnosis_code']
        }
    }
    chunks.append(demo_chunk)
    
    # 2. Lab Results Chunk
    if pd.notna(record.get('lab_test')):
        lab_content = f"Lab results: {record['lab_test']}: {record['lab_value']} {record.get('lab_unit', '')}."
        
        # Add noise to lab values for privacy levels
        if privacy_level in ['moderate', 'high'] and record.get('lab_value'):
            try:
                value = float(record['lab_value'])
                if privacy_level == 'moderate':
                    noise = np.random.normal(0, value * 0.1)
                    value = round(value + noise, 1)
                elif privacy_level == 'high':
                    # Round to nearest 5 or 10
                    value = round(value / 5) * 5
                lab_content = f"Lab results: {record['lab_test']}: ~{value} {record.get('lab_unit', '')}."
            except:
                pass
        
        lab_chunk = {
            'text': protected_header + lab_content,
            'metadata': {
                'patient_id': pid,
                'chunk_type': 'lab_results',
                'lab_test': record['lab_test']
            }
        }
        chunks.append(lab_chunk)
    
    # 3. Medications Chunk
    if pd.notna(record.get('medication')):
        med_content = f"Prescribed medication: {record['medication']}."
        
        if privacy_level in ['moderate', 'high']:
            provider = "[PROVIDER_REDACTED]" if privacy_level == 'high' else record.get('provider_name', 'Unknown')
            facility = "[FACILITY_REDACTED]" if privacy_level == 'high' else record.get('facility_name', 'Unknown')
        else:
            provider = record.get('provider_name', 'Unknown')
            facility = record.get('facility_name', 'Unknown')
        
        med_content += f" Provider: {provider} at {facility}."
        
        med_chunk = {
            'text': protected_header + med_content,
            'metadata': {
                'patient_id': pid,
                'chunk_type': 'medications',
                'provider': provider
            }
        }
        chunks.append(med_chunk)
    
    # 4. Clinical Notes Chunk (if not already used for header)
    if pd.notna(record.get('notes')):
        # Remove the patient header part from notes to avoid duplication
        notes_content = record['notes']
        # Try to remove the header portion we already extracted
        notes_content = re.sub(r'^Patient .+? (?:presents|arrived)', 'Presents', notes_content)
        
        notes_chunk = {
            'text': protected_header + notes_content,
            'metadata': {
                'patient_id': pid,
                'chunk_type': 'clinical_notes'
            }
        }
        chunks.append(notes_chunk)
    
    return chunks

# ---------------------------
# Main Setup
# ---------------------------
def setup_consistent_chromadb():
    SITE_NAME = 'site1'
    DB_PATH = './chromadb_site1_db'
    CSV_PATH = '/mnt/user-data/uploads/site1_medical_data_large.csv'
    
    PRIVACY_LEVELS = {
        'none': float('inf'),
        'low': 10.0,
        'moderate': 1.0,
        'high': 0.1
    }
    
    print("🚀 Setting up consistent ChromaDB with standardized PHI handling...")
    
    # Load embedding model
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    
    # Create client
    client = PersistentClient(path=DB_PATH)
    
    # Create collections
    collections = {}
    for level, epsilon in PRIVACY_LEVELS.items():
        col_name = f"{SITE_NAME}_{level}_privacy"
        try:
            client.delete_collection(name=col_name)
            print(f"Deleted existing collection {col_name}")
        except:
            pass
        
        collections[level] = client.create_collection(
            name=col_name,
            embedding_function=embedding_fn,
            metadata={
                "site_name": SITE_NAME,
                "privacy_level": level,
                "epsilon": str(epsilon)
            }
        )
        print(f"Created collection {col_name} (ε={epsilon})")
    
    # Load CSV
    print(f"📂 Loading CSV: {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)
    print(f"Loaded {len(df)} rows.")
    
    # Process and store for each privacy level
    print("📥 Processing with consistent PHI handling...")
    
    for level, col in collections.items():
        print(f"\nProcessing privacy level: {level}")
        docs, metas, ids = [], [], []
        
        for idx, record in df.iterrows():
            # Create chunks with consistent PHI for this privacy level
            chunks = chunk_record_with_consistent_phi(record, privacy_level=level)
            
            for i, chunk in enumerate(chunks):
                docs.append(chunk['text'])
                metas.append(chunk['metadata'])
                ids.append(f"{record['patient_id']}_{i}_{level}")
            
            # Batch insert every 100
            if len(docs) >= 100:
                col.add(documents=docs, metadatas=metas, ids=ids)
                docs, metas, ids = [], [], []
        
        # Insert remaining
        if docs:
            col.add(documents=docs, metadatas=metas, ids=ids)
        
        print(f"Stored {col.count()} chunks in {col.name}")
    
    # Test consistency
    print("\n🔍 Testing consistency across different queries...")
    test_queries = [
        "sleep apnea and elevated creatinine",
        "patients with general consultation",
        "diabetes medications"
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        for level in ['none', 'moderate']:
            res = collections[level].query(query_texts=[query], n_results=1)
            if res['documents'][0]:
                doc = res['documents'][0][0]
                # Extract just the patient header for comparison
                header_match = re.search(r'^(.*?)\. ', doc)
                if header_match:
                    print(f"  {level:8} - {header_match.group(1)[:80]}...")
    
    print("\n✅ Setup complete with consistent PHI handling!")

if __name__ == "__main__":
    setup_consistent_chromadb()
