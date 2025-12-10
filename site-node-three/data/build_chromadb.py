#!/usr/bin/env python3
"""
Enhanced ChromaDB Setup with Complete Patient Information
Ensures age, contact details, and address appear in ALL chunks
with appropriate privacy-level redaction
Author: Dilip Thakur
"""

import pandas as pd
import numpy as np
from chromadb import PersistentClient
from chromadb.utils import embedding_functions
import re
import os
import sys
import argparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CHROMA_DB_PATH = os.getenv(
    "CHROMA_DB_PATH",
    os.path.join(BASE_DIR, "database")
)
DEFAULT_SITE_NAME = os.getenv("CHROMA_SITE_NAME", "site3")

def resolve_site_name(fallback: str = DEFAULT_SITE_NAME) -> str:
    """
    Determine site name from env or directory (supports site-node-three style names).
    """
    env_val = os.getenv("CHROMA_SITE_NAME")
    if env_val:
        return env_val
    base = os.path.basename(os.path.abspath(os.getcwd()))
    if base.endswith("site-node-one"):
        return "site1"
    if base.endswith("site-node-two"):
        return "site2"
    if base.endswith("site-node-three"):
        return "site3"
    return fallback

# ---------------------------
# Differential Privacy Processor
# --------------------------- 
class DifferentialPrivacyProcessor:
    def __init__(self, epsilon: float = 1.0):
        self.epsilon = epsilon
        self.sensitivity = 1.0

    def generalize_age(self, age: int, level: str = 'moderate') -> str:
        """Generalize age based on privacy level"""
        try:
            age = int(age)
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
        except:
            return "Unknown"
    
    def redact_phone(self, phone: str, level: str) -> str:
        """Redact phone number based on privacy level"""
        if not phone or pd.isna(phone):
            return "[PHONE_UNKNOWN]"
        
        phone_str = str(phone)
        if level == 'none':
            return phone_str
        elif level == 'low':
            # Keep area code and last 4 digits
            if len(phone_str) >= 10:
                return re.sub(r'(\d{3})[\d\-\.\s]*(\d{4})', r'\1-XXX-\2', phone_str)
            return phone_str[:3] + "-XXX-XXXX"
        elif level == 'moderate':
            # Keep only area code
            if len(phone_str) >= 3:
                return phone_str[:3] + "-XXX-XXXX"
            return "XXX-XXX-XXXX"
        else:  # high
            return "[PHONE_REDACTED]"
    
    def redact_address(self, address: str, level: str) -> str:
        """Redact address based on privacy level"""
        if not address or pd.isna(address):
            return "[ADDRESS_UNKNOWN]"
        
        address_str = str(address)
        if level == 'none':
            return address_str
        elif level == 'low':
            # Keep city and state only
            parts = address_str.split(',')
            if len(parts) >= 2:
                # Try to keep last two parts (usually city, state)
                return f"[STREET_REDACTED], {parts[-2].strip()}, {parts[-1].strip()}"
            return address_str
        elif level == 'moderate':
            # Keep state only
            parts = address_str.split(',')
            if len(parts) >= 1:
                # Extract state (usually last part or second to last)
                state_part = parts[-1].strip()
                # Extract state code (2 letters)
                state_match = re.search(r'\b[A-Z]{2}\b', state_part)
                if state_match:
                    return f"[ADDRESS_REDACTED], {state_match.group()}"
            return "[ADDRESS_REDACTED], USA"
        else:  # high
            return "[ADDRESS_REDACTED]"

    def apply_privacy_to_patient_header(self, header: str, privacy_level: str) -> str:
        """
        Apply consistent privacy transformations to patient header
        """
        if privacy_level == 'none':
            return header
        
        elif privacy_level == 'low':
            # Partial redaction
            header = re.sub(r'SSN: \d{3}-\d{2}-(\d{4})', r'SSN: XXX-XX-\1', header)
            header = re.sub(r'(\w+)@(\w+\.\w+)', r'***@\2', header)
            
        elif privacy_level == 'moderate':
            # More redaction
            header = re.sub(r'Patient (\w)\w* (\w)\w*', r'Patient \1*** \2***', header)
            header = re.sub(r'SSN: \d{3}-\d{2}-\d{4}', 'SSN: XXX-XX-XXXX', header)
            header = re.sub(r'DOB: \d{2}/\d{2}/\d{4}', 'DOB: [REDACTED]', header)
            header = re.sub(r'\w+@\w+\.\w+', '[EMAIL_REDACTED]', header)
            
        elif privacy_level == 'high':
            # Complete redaction
            header = re.sub(r'Patient \w+ \w+', 'Patient [NAME_REDACTED]', header)
            header = re.sub(r'SSN: \d{3}-\d{2}-\d{4}', 'SSN: [REDACTED]', header)
            header = re.sub(r'DOB: \d{2}/\d{2}/\d{4}', 'DOB: [REDACTED]', header)
            header = re.sub(r'Email: .+?\.', 'Email: [EMAIL_REDACTED].', header)
            header = re.sub(r'Insurance: \w+\d+', 'Insurance: [REDACTED]', header)
            
        return header

# ---------------------------
# Enhanced Patient Header Creation
# ---------------------------
def extract_patient_info(record):
    """
    Extract all patient information from the record
    Returns a dictionary with all patient details
    """
    info = {}
    
    # Extract from notes if available (most complete source)
    if 'notes' in record and pd.notna(record['notes']):
        notes = str(record['notes'])
        
        # Extract name
        name_match = re.search(r'(?:Patient|ED patient|Oncology patient) ([A-Z][a-z]+ [A-Z][a-z]+)', notes)
        if name_match:
            info['name'] = name_match.group(1)
        
        # Extract DOB
        dob_match = re.search(r'DOB: (\d{2}/\d{2}/\d{4})', notes)
        if dob_match:
            info['dob'] = dob_match.group(1)
        
        # Extract SSN
        ssn_match = re.search(r'SSN: ([\d\-]+)', notes)
        if ssn_match:
            info['ssn'] = ssn_match.group(1)
        
        # Extract phone
        phone_match = re.search(r'Contact: ([\d\.\-\+\(\)x\s]+)(?:\.|\,)', notes)
        if phone_match:
            info['phone'] = phone_match.group(1).strip()
        
        # Extract address
        addr_match = re.search(r'(?:Lives at|Address:) ([^\.]+)\.', notes)
        if addr_match:
            info['address'] = addr_match.group(1).strip()
        
        # Extract email
        email_match = re.search(r'Email: ([\w\.\-]+@[\w\.\-]+)', notes)
        if email_match:
            info['email'] = email_match.group(1)
    
    # Fill in from direct columns if not found in notes
    info['patient_id'] = record.get('patient_id', 'Unknown')
    info['age'] = record.get('age', 'Unknown')
    info['gender'] = record.get('gender', 'Unknown')
    
    # Parse PHI elements if available
    if 'phi_elements' in record and pd.notna(record['phi_elements']):
        phi_str = str(record['phi_elements'])
        for element in phi_str.split('|'):
            if ':' in element:
                key, value = element.split(':', 1)
                if key == 'name' and 'name' not in info:
                    info['name'] = value
                elif key == 'phone' and 'phone' not in info:
                    info['phone'] = value
                elif key == 'address' and 'address' not in info:
                    info['address'] = value
                elif key == 'ssn' and 'ssn' not in info:
                    info['ssn'] = value
                elif key == 'dob' and 'dob' not in info:
                    info['dob'] = value
                elif key == 'email' and 'email' not in info:
                    info['email'] = value
    
    return info

def create_comprehensive_patient_header(info, privacy_level='none'):
    """
    Create a comprehensive patient header with ALL information
    This will be prepended to EVERY chunk
    """
    dp = DifferentialPrivacyProcessor()
    
    # Start with patient name
    if privacy_level == 'none':
        name = info.get('name', f"Patient {info.get('patient_id', 'Unknown')}")
    elif privacy_level == 'low':
        name = info.get('name', f"Patient {info.get('patient_id', 'Unknown')}")
    elif privacy_level == 'moderate':
        if 'name' in info and info['name']:
            parts = info['name'].split()
            if len(parts) >= 2:
                name = f"{parts[0][0]}*** {parts[-1][0]}***"
            else:
                name = f"{parts[0][0]}***"
        else:
            name = f"Patient {info.get('patient_id', 'Unknown')}"
    else:  # high
        name = "[NAME_REDACTED]"
    
    header = f"Patient: {name}"
    
    # Add age with generalization
    if 'age' in info and info['age'] != 'Unknown':
        age_str = dp.generalize_age(info['age'], privacy_level)
        header += f", Age: {age_str}"
    
    # Add gender (always shown)
    if 'gender' in info:
        header += f", Gender: {info['gender']}"
    
    # Add contact phone
    if 'phone' in info:
        phone_str = dp.redact_phone(info['phone'], privacy_level)
        header += f", Phone: {phone_str}"
    
    # Add address
    if 'address' in info:
        addr_str = dp.redact_address(info['address'], privacy_level)
        header += f", Address: {addr_str}"
    
    # Add DOB (if not high privacy)
    if 'dob' in info and privacy_level in ['none', 'low']:
        header += f", DOB: {info['dob']}"
    elif 'dob' in info and privacy_level == 'moderate':
        # Show year only
        year_match = re.search(r'\d{4}', info['dob'])
        if year_match:
            header += f", Birth Year: {year_match.group()}"
    
    # Add SSN with appropriate redaction
    if 'ssn' in info:
        ssn = info['ssn']
        if privacy_level == 'none':
            header += f", SSN: {ssn}"
        elif privacy_level == 'low' and len(str(ssn)) >= 9:
            header += f", SSN: XXX-XX-{str(ssn)[-4:]}"
        elif privacy_level == 'moderate':
            header += ", SSN: XXX-XX-XXXX"
        # High privacy: don't show SSN at all
    
    return header + ". "

def chunk_record_with_complete_info(record, privacy_level='none', site_type='general'):
    """
    Create chunks where EVERY chunk has complete patient information
    including age, phone, and address with appropriate privacy
    """
    chunks = []
    pid = record.get('patient_id', 'Unknown')
    
    # Extract all patient information
    patient_info = extract_patient_info(record)
    
    # Create comprehensive header with ALL details
    patient_header = create_comprehensive_patient_header(patient_info, privacy_level)
    
    # Now create chunks, each with the complete patient header
    
    # 1. Demographics + Diagnosis Chunk
    if 'diagnosis_description' in record and pd.notna(record['diagnosis_description']):
        demo_content = f"Diagnosis: {record['diagnosis_description']} (ICD-10: {record.get('diagnosis_code', 'Unknown')}). "
        demo_content += f"Chief complaint: {record.get('chief_complaint', 'Unknown')}."
        
        # Add site-specific info
        if site_type == 'oncology' and 'department' in record:
            demo_content += f" Department: {record['department']}."
        elif site_type == 'emergency' and 'triage_level' in record:
            demo_content += f" Triage level: {record['triage_level']}."
            if 'arrival_time' in record:
                demo_content += f" Arrival: {record['arrival_time']}."
        
        demo_chunk = {
            'text': patient_header + demo_content,
            'metadata': {
                'patient_id': pid,
                'chunk_type': 'demographics',
                'diagnosis_code': record.get('diagnosis_code', 'Unknown'),
                'site_type': site_type,
                'has_complete_info': True
            }
        }
        chunks.append(demo_chunk)
    
    # 2. Lab Results Chunk
    if 'lab_test' in record and pd.notna(record.get('lab_test')):
        lab_content = f"Lab results: {record['lab_test']}: {record.get('lab_value', 'Unknown')} {record.get('lab_unit', '')}."
        
        # Add noise to lab values for moderate/high privacy
        if privacy_level in ['moderate', 'high'] and record.get('lab_value'):
            try:
                value = float(record['lab_value'])
                if privacy_level == 'moderate':
                    noise = np.random.normal(0, value * 0.1)
                    value = round(value + noise, 1)
                elif privacy_level == 'high':
                    value = round(value / 5) * 5
                lab_content = f"Lab results: {record['lab_test']}: ~{value} {record.get('lab_unit', '')}."
            except:
                pass
        
        lab_chunk = {
            'text': patient_header + lab_content,
            'metadata': {
                'patient_id': pid,
                'chunk_type': 'lab_results',
                'lab_test': record.get('lab_test', 'Unknown'),
                'site_type': site_type,
                'has_complete_info': True
            }
        }
        chunks.append(lab_chunk)
    
    # 3. Medications Chunk
    if 'medication' in record and pd.notna(record.get('medication')):
        med_content = f"Prescribed medication: {record['medication']}."
        
        if 'dosage' in record and pd.notna(record['dosage']):
            med_content += f" Dosage: {record['dosage']}."
        
        if privacy_level in ['moderate', 'high']:
            provider = "[PROVIDER_REDACTED]" if privacy_level == 'high' else record.get('provider_name', 'Unknown')
            facility = "[FACILITY_REDACTED]" if privacy_level == 'high' else record.get('facility_name', 'Unknown')
        else:
            provider = record.get('provider_name', 'Unknown')
            facility = record.get('facility_name', 'Unknown')
        
        med_content += f" Provider: {provider} at {facility}."
        
        med_chunk = {
            'text': patient_header + med_content,
            'metadata': {
                'patient_id': pid,
                'chunk_type': 'medications',
                'provider': provider,
                'site_type': site_type,
                'has_complete_info': True
            }
        }
        chunks.append(med_chunk)
    
    # 4. Emergency-specific: Vital Signs
    if site_type == 'emergency' and 'vital_signs' in record and pd.notna(record['vital_signs']):
        vital_content = f"Vital signs: {record['vital_signs']}."
        if 'intervention' in record:
            vital_content += f" Intervention: {record['intervention']}."
        if 'disposition' in record:
            vital_content += f" Disposition: {record['disposition']}."
        
        vital_chunk = {
            'text': patient_header + vital_content,
            'metadata': {
                'patient_id': pid,
                'chunk_type': 'vital_signs',
                'site_type': site_type,
                'has_complete_info': True
            }
        }
        chunks.append(vital_chunk)
    
    # 5. Clinical Notes (simplified to avoid duplication)
    if 'notes' in record and pd.notna(record.get('notes')):
        # Just add key clinical info, not the full notes (to avoid duplication)
        notes_content = "Clinical notes available with additional details."
        
        notes_chunk = {
            'text': patient_header + notes_content,
            'metadata': {
                'patient_id': pid,
                'chunk_type': 'clinical_notes',
                'site_type': site_type,
                'has_complete_info': True
            }
        }
        chunks.append(notes_chunk)
    
    return chunks

# ---------------------------
# Site Configuration
# ---------------------------
def get_site_config(site_number=DEFAULT_SITE_NAME):
    """Get configuration for each site"""
    configs = {
        'site1': {
            'name': 'site1',
            'type': 'general',
            'csv_filename': 'site1_medical_data_large.csv',
            'db_path': DEFAULT_CHROMA_DB_PATH,
            'description': 'General Medical Site'
        },
        'site2': {
            'name': 'site2',
            'type': 'oncology',
            'csv_filename': 'site2_oncology_data_large.csv',
            'db_path': DEFAULT_CHROMA_DB_PATH,
            'description': 'Oncology Site'
        },
        'site3': {
            'name': 'site3',
            'type': 'emergency',
            'csv_filename': 'site3_emergency_data_large.csv',
            'db_path': DEFAULT_CHROMA_DB_PATH,
            'description': 'Emergency Department Site'
        }
    }
    return configs.get(site_number, configs.get(DEFAULT_SITE_NAME))

# ---------------------------
# Main Setup Function
# ---------------------------
def setup_enhanced_chromadb(site_number=DEFAULT_SITE_NAME):
    """Set up ChromaDB with complete patient information in all chunks"""
    
    env_site = resolve_site_name(site_number)
    site_config = get_site_config(env_site)
    if not site_config:
        print(f"❌ Invalid site number: {site_number}")
        return
    
    SITE_NAME = site_config['name']
    SITE_TYPE = site_config['type']
    DB_PATH = os.getenv("CHROMA_DB_PATH", site_config['db_path'])
    CSV_PATH = os.getenv(
        "CHROMA_SOURCE_CSV",
        os.path.join(BASE_DIR, site_config['csv_filename'])
    )
    
    PRIVACY_LEVELS = {
        'none': float('inf'),
        'low': 10.0,
        'moderate': 1.0,
        'high': 0.1
    }
    
    print(f"🚀 Enhanced Setup for {site_config['description']}")
    print(f"   Now including: Age, Phone, Address in ALL chunks")
    print("=" * 60)
    
    if not os.path.exists(CSV_PATH):
        print(f"❌ CSV file not found: {CSV_PATH}")
        return
    
    # Load embedding model
    print("📦 Loading embedding model...")
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
            print(f"  Deleted existing: {col_name}")
        except:
            pass
        
        collections[level] = client.create_collection(
            name=col_name,
            embedding_function=embedding_fn,
            metadata={
                "site_name": SITE_NAME,
                "site_type": SITE_TYPE,
                "privacy_level": level,
                "epsilon": str(epsilon),
                "enhanced_version": "2.0"
            }
        )
        print(f"  ✅ Created: {col_name} (ε={epsilon})")
    
    # Load CSV
    print(f"\n📂 Loading data...")
    df = pd.read_csv(CSV_PATH)
    print(f"  Loaded {len(df)} records")
    
    # Process for each privacy level
    print("\n📥 Processing with complete patient information...")
    
    for level, col in collections.items():
        print(f"\n  Privacy level: {level}")
        docs, metas, ids = [], [], []
        
        for idx, record in df.iterrows():
            # Create chunks with COMPLETE patient info
            chunks = chunk_record_with_complete_info(
                record, 
                privacy_level=level, 
                site_type=SITE_TYPE
            )
            
            for i, chunk in enumerate(chunks):
                docs.append(chunk['text'])
                metas.append(chunk['metadata'])
                ids.append(f"{record.get('patient_id', f'PAT{idx}')}_{i}_{level}")
            
            # Batch insert
            if len(docs) >= 100:
                col.add(documents=docs, metadatas=metas, ids=ids)
                docs, metas, ids = [], [], []
        
        # Insert remaining
        if docs:
            col.add(documents=docs, metadatas=metas, ids=ids)
        
        print(f"    ✅ Stored {col.count()} chunks")
    
    # Test to verify complete info
    print("\n🔍 Verifying complete patient information...")
    test_query = "patient diagnosis"
    
    for level in ['none', 'moderate', 'high']:
        res = collections[level].query(query_texts=[test_query], n_results=1)
        if res['documents'][0]:
            doc = res['documents'][0][0]
            print(f"\n  {level.upper()} Privacy Sample:")
            # Check for key fields
            has_age = "Age:" in doc
            has_phone = "Phone:" in doc
            has_address = "Address:" in doc
            print(f"    Has Age: {'✅' if has_age else '❌'}")
            print(f"    Has Phone: {'✅' if has_phone else '❌'}")
            print(f"    Has Address: {'✅' if has_address else '❌'}")
            print(f"    Preview: {doc[:150]}...")
    
    print("\n✅ Enhanced setup complete!")
    print(f"   All chunks now include: Age, Phone, Address")
    print(f"   Database: {DB_PATH}")

# ---------------------------
# Main Entry Point
# ---------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Enhanced ChromaDB setup with complete patient info')
    parser.add_argument('--site', type=str, default='site3',
                       choices=['site1', 'site2', 'site3'],
                       help='Site to set up')
    
    args = parser.parse_args()
    setup_enhanced_chromadb(args.site)
