#!/usr/bin/env python3
"""
Revised ChromaDB Setup with Differential Privacy for Distributed RAG
Architecture: 1 Database per Site, 4 Collections per Database (for privacy levels)
This implements T1, T2, and T3 tasks for the Site RAG Service
Author: Dilip Thakur
"""

import pandas as pd
import numpy as np
import chromadb
from chromadb.utils import embedding_functions
import hashlib
import re
from typing import List, Dict, Tuple
import json
from datetime import datetime
import random
import os

# Install required packages:
# pip install chromadb pandas numpy sentence-transformers

class DifferentialPrivacyProcessor:
    """
    Implements differential privacy mechanisms for PHI/PII protection
    Supports multiple privacy levels for testing
    """
    
    def __init__(self, epsilon: float = 1.0):
        """
        Initialize with privacy budget epsilon
        Lower epsilon = more privacy, less utility
        Higher epsilon = less privacy, more utility
        
        Recommended values:
        - epsilon = 0.1: High privacy (maximum noise)
        - epsilon = 1.0: Moderate privacy (balanced)
        - epsilon = 10.0: Low privacy (minimal noise)
        - epsilon = float('inf'): No privacy (no noise)
        """
        self.epsilon = epsilon
        self.sensitivity = 1.0  # Sensitivity for Laplace mechanism
        
    def add_laplace_noise(self, value: float) -> float:
        """Add Laplace noise to numerical values"""
        if self.epsilon == float('inf'):
            return value
        scale = self.sensitivity / self.epsilon
        noise = np.random.laplace(0, scale)
        return value + noise
    
    def generalize_age(self, age: int, level: str = 'moderate') -> str:
        """Generalize age to ranges based on privacy level"""
        if level == 'none':
            return str(age)
        elif level == 'low':
            # 5-year ranges
            lower = (age // 5) * 5
            return f"{lower}-{lower+4}"
        elif level == 'moderate':
            # 10-year ranges
            lower = (age // 10) * 10
            return f"{lower}-{lower+9}"
        else:  # high
            # 20-year ranges
            lower = (age // 20) * 20
            return f"{lower}-{lower+19}"
    
    def redact_phi(self, text: str, phi_elements: str, privacy_level: str) -> str:
        """
        Redact PHI based on privacy level
        
        Privacy levels:
        - none: No redaction (epsilon = inf)
        - low: Partial redaction (epsilon = 10)
        - moderate: Standard redaction (epsilon = 1)
        - high: Complete redaction (epsilon = 0.1)
        """
        if privacy_level == 'none':
            return text
        
        # Parse PHI elements
        phi_items = {}
        if phi_elements and '|' in phi_elements:
            for item in phi_elements.split('|'):
                if ':' in item:
                    key, value = item.split(':', 1)
                    phi_items[key] = value
        
        redacted_text = text
        
        # Apply redaction based on privacy level
        if privacy_level == 'high':
            # Complete redaction
            for key, value in phi_items.items():
                if key == 'name':
                    redacted_text = redacted_text.replace(value, '[NAME_REDACTED]')
                elif key == 'ssn':
                    redacted_text = redacted_text.replace(value, '[SSN_REDACTED]')
                elif key == 'dob':
                    redacted_text = redacted_text.replace(value, '[DOB_REDACTED]')
                elif key == 'phone':
                    redacted_text = redacted_text.replace(value, '[PHONE_REDACTED]')
                elif key == 'address':
                    redacted_text = redacted_text.replace(value, '[ADDRESS_REDACTED]')
                elif key == 'email':
                    redacted_text = redacted_text.replace(value, '[EMAIL_REDACTED]')
                    
        elif privacy_level == 'moderate':
            # Partial redaction - keep some info for utility
            for key, value in phi_items.items():
                if key == 'name' and value:
                    # Keep first initial, last initial
                    parts = value.split()
                    if len(parts) >= 2:
                        masked = f"{parts[0][0]}*** {parts[-1][0]}***"
                        redacted_text = redacted_text.replace(value, masked)
                elif key == 'ssn' and value:
                    # Keep last 4 digits
                    redacted_text = redacted_text.replace(value, f"XXX-XX-{value[-4:]}")
                elif key == 'phone' and value:
                    # Keep area code
                    if len(value) >= 10:
                        redacted_text = redacted_text.replace(value, f"{value[:3]}-XXX-XXXX")
                elif key == 'email' and value:
                    # Keep domain
                    if '@' in value:
                        domain = value.split('@')[1]
                        redacted_text = redacted_text.replace(value, f"***@{domain}")
                        
        elif privacy_level == 'low':
            # Minimal redaction - high utility
            for key, value in phi_items.items():
                if key == 'ssn' and value:
                    # Mask middle digits only
                    if len(value) >= 11:
                        redacted_text = redacted_text.replace(value, f"{value[:3]}-XX-{value[-4:]}")
                elif key == 'email' and value:
                    # Partial email masking
                    if '@' in value:
                        local, domain = value.split('@')
                        if len(local) > 2:
                            masked = f"{local[:2]}***@{domain}"
                            redacted_text = redacted_text.replace(value, masked)
        
        return redacted_text
    
    def add_noise_to_lab_value(self, value: float, privacy_level: str) -> float:
        """Add calibrated noise to lab values based on privacy level"""
        if privacy_level == 'none':
            return value
        elif privacy_level == 'low':
            # ±5% noise
            noise = np.random.normal(0, value * 0.05)
        elif privacy_level == 'moderate':
            # ±10% noise
            noise = np.random.normal(0, value * 0.10)
        else:  # high
            # ±20% noise
            noise = np.random.normal(0, value * 0.20)
        
        return round(value + noise, 2)


class SiteRAGDatabase:
    """
    Manages a single ChromaDB database for a site with multiple privacy-level collections
    Architecture: 1 Database with 4 Collections (none, low, moderate, high privacy)
    """
    
    def __init__(self, site_name: str, site_type: str, db_path: str = None):
        """
        Initialize a site-specific database
        
        Args:
            site_name: Unique identifier for the site (e.g., 'site1')
            site_type: Type of site (e.g., 'general', 'oncology', 'emergency')
            db_path: Path for the database storage
        """
        self.site_name = site_name
        self.site_type = site_type
        
        # Create database path
        if db_path is None:
            #db_path = f"/home/claude/chroma_{site_name}_db"
            db_path = f"./chroma_{site_name}_db"
        
        # Initialize ChromaDB client for this specific site
        self.chroma_client = chromadb.PersistentClient(path=db_path)
        
        # Use sentence transformer for embeddings
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"  # Lightweight model good for medical text
        )
        
        # Privacy levels configuration
        self.privacy_levels = {
            'none': {
                'epsilon': float('inf'), 
                'description': 'No privacy protection - baseline for testing'
            },
            'low': {
                'epsilon': 10.0, 
                'description': 'Low privacy (ε=10) - internal analytics'
            },
            'moderate': {
                'epsilon': 1.0, 
                'description': 'Moderate privacy (ε=1) - cross-site queries'
            },
            'high': {
                'epsilon': 0.1, 
                'description': 'High privacy (ε=0.1) - public/external access'
            }
        }
        
        # Store collections for this database
        self.collections = {}
        
        print(f"Initialized database for {site_name} ({site_type})")
    
    def create_collections(self):
        """Create 4 collections within this database for different privacy levels"""
        for level_name, level_config in self.privacy_levels.items():
            collection_name = f"{self.site_name}_{level_name}_privacy"
            
            # Delete if exists (for clean setup)
            try:
                self.chroma_client.delete_collection(name=collection_name)
                print(f"  Deleted existing collection: {collection_name}")
            except:
                pass
            
            # Create new collection
            self.collections[level_name] = self.chroma_client.create_collection(
                name=collection_name,
                embedding_function=self.embedding_function,
                metadata={
                    "site_name": self.site_name,
                    "site_type": self.site_type,
                    "privacy_level": level_name,
                    "epsilon": str(level_config['epsilon']),
                    "description": level_config['description']
                }
            )
            
            print(f"  Created collection: {collection_name} (ε={level_config['epsilon']})")
    
    def chunk_record(self, record: pd.Series) -> List[Dict]:
        """
        T1: Chunk a single patient record into smaller segments
        Returns list of chunks with metadata
        """
        chunks = []
        patient_id = record['patient_id']
        
        # Chunk 1: Demographics and Diagnosis
        demo_chunk = {
            'text': f"Patient {patient_id} is a {record['age']} year old {record['gender']}. "
                   f"Diagnosis: {record['diagnosis_description']} (ICD-10: {record['diagnosis_code']}). "
                   f"Chief complaint: {record['chief_complaint']}.",
            'metadata': {
                'patient_id': patient_id,
                'chunk_type': 'demographics',
                'diagnosis_code': record['diagnosis_code'],
                'site': self.site_name
            }
        }
        chunks.append(demo_chunk)
        
        # Chunk 2: Lab Results
        if pd.notna(record.get('lab_test')):
            lab_chunk = {
                'text': f"Lab results for patient {patient_id}: "
                       f"{record['lab_test']}: {record['lab_value']} {record.get('lab_unit', '')}.",
                'metadata': {
                    'patient_id': patient_id,
                    'chunk_type': 'lab_results',
                    'lab_test': record['lab_test'],
                    'site': self.site_name
                }
            }
            chunks.append(lab_chunk)
        
        # Chunk 3: Medications
        if pd.notna(record.get('medication')):
            med_chunk = {
                'text': f"Patient {patient_id} prescribed: {record['medication']}. "
                       f"Provider: {record.get('provider_name', 'Unknown')} at {record.get('facility_name', 'Unknown')}.",
                'metadata': {
                    'patient_id': patient_id,
                    'chunk_type': 'medications',
                    'provider': record.get('provider_name', 'Unknown'),
                    'site': self.site_name
                }
            }
            chunks.append(med_chunk)
        
        # Chunk 4: Clinical Notes
        if pd.notna(record.get('notes')):
            notes_chunk = {
                'text': record['notes'],
                'metadata': {
                    'patient_id': patient_id,
                    'chunk_type': 'clinical_notes',
                    'visit_date': str(record.get('visit_date', '')),
                    'site': self.site_name
                }
            }
            chunks.append(notes_chunk)
        
        # Site-specific chunks
        if self.site_type == 'emergency' and 'vital_signs' in record:
            vital_chunk = {
                'text': f"Vital signs for {patient_id}: {record['vital_signs']}. "
                       f"Triage level: {record.get('triage_level', 'Unknown')}.",
                'metadata': {
                    'patient_id': patient_id,
                    'chunk_type': 'vital_signs',
                    'triage_level': str(record.get('triage_level', '')),
                    'site': self.site_name
                }
            }
            chunks.append(vital_chunk)
        
        return chunks
    
    def process_and_store(self, data_path: str, sample_size: int = None):
        """
        Main pipeline: Load data, apply differential privacy, and store in collections
        """
        print(f"\nProcessing data for {self.site_name} ({self.site_type})")
        print("=" * 60)
        
        # Load data
        df = pd.read_csv(data_path)
        if sample_size:
            df = df.head(sample_size)
        print(f"Loaded {len(df)} records from {os.path.basename(data_path)}")
        
        # Create collections for this database
        self.create_collections()
        
        # Process each privacy level
        for privacy_level, collection in self.collections.items():
            print(f"\n  Processing privacy level: {privacy_level}")
            
            dp_processor = DifferentialPrivacyProcessor(
                epsilon=self.privacy_levels[privacy_level]['epsilon']
            )
            
            documents = []
            metadatas = []
            ids = []
            
            # Process each record
            for idx, record in df.iterrows():
                # T1: Chunk the record
                chunks = self.chunk_record(record)
                
                # T2: Apply differential privacy to each chunk
                for chunk_idx, chunk in enumerate(chunks):
                    # Apply PHI redaction
                    if 'phi_elements' in record and pd.notna(record['phi_elements']):
                        chunk['text'] = dp_processor.redact_phi(
                            chunk['text'],
                            record['phi_elements'],
                            privacy_level
                        )
                    
                    # Add noise to age if present in text
                    if 'age' in record and pd.notna(record['age']):
                        age_range = dp_processor.generalize_age(
                            int(record['age']),
                            privacy_level
                        )
                        chunk['text'] = re.sub(
                            f"{int(record['age'])} year old",
                            f"{age_range} year old",
                            chunk['text']
                        )
                    
                    # Add noise to lab values if it's a lab chunk
                    if chunk['metadata']['chunk_type'] == 'lab_results' and 'lab_value' in record:
                        try:
                            original_value = float(record['lab_value'])
                            noisy_value = dp_processor.add_noise_to_lab_value(
                                original_value,
                                privacy_level
                            )
                            chunk['text'] = re.sub(
                                str(record['lab_value']),
                                str(noisy_value),
                                chunk['text']
                            )
                        except:
                            pass  # Skip if not numeric
                    
                    # Prepare for ChromaDB
                    documents.append(chunk['text'])
                    metadatas.append(chunk['metadata'])
                    ids.append(f"{record['patient_id']}_{chunk_idx}_{privacy_level}")
                
                # Add in batches of 100 for efficiency
                if len(documents) >= 100:
                    collection.add(
                        documents=documents,
                        metadatas=metadatas,
                        ids=ids
                    )
                    documents = []
                    metadatas = []
                    ids = []
            
            # Add remaining documents
            if documents:
                collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
            
            print(f"    Stored {collection.count()} chunks in {collection.name}")
        
        print(f"\n  Total collections in {self.site_name} database: {len(self.collections)}")
    
    def query(self, query_text: str, privacy_level: str = 'moderate', n_results: int = 5):
        """
        Query a specific privacy level collection within this database
        """
        if privacy_level not in self.collections:
            print(f"Privacy level {privacy_level} not found in {self.site_name}")
            return None
        
        collection = self.collections[privacy_level]
        results = collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        
        return {
            'site': self.site_name,
            'site_type': self.site_type,
            'privacy_level': privacy_level,
            'epsilon': self.privacy_levels[privacy_level]['epsilon'],
            'results': results
        }


def setup_all_sites():
    """
    Set up all three sites with their own databases
    Total: 3 databases, 12 collections (4 per database)
    """
    print("\n" + "="*70)
    print("SETTING UP CHROMADB WITH DIFFERENTIAL PRIVACY")
    print("Architecture: 3 Databases, 4 Collections per Database")
    print("="*70)
    
    # Site configurations
    sites_config = [
        {
            'site_name': 'site1',
            'site_type': 'general',
            'data_path': '/mnt/user-data/uploads/site1_medical_data_large.csv',
            'description': 'General Medical Center'
        },
        # {
        #     'site_name': 'site2',
        #     'site_type': 'oncology',
        #     'data_path': '/mnt/user-data/uploads/site2_oncology_data_large.csv',
        #     'description': 'Regional Cancer Institute'
        # },
        # {
        #     'site_name': 'site3',
        #     'site_type': 'emergency',
        #     'data_path': '/mnt/user-data/uploads/site3_emergency_data_large.csv',
        #     'description': 'Emergency Department'
        # }
    ]
    
    databases = []
    
    # Create and populate each site's database
    for config in sites_config:
        print(f"\n{'='*70}")
        print(f"Setting up: {config['description']}")
        print(f"{'='*70}")
        
        # Create database for this site
        site_db = SiteRAGDatabase(
            site_name=config['site_name'],
            site_type=config['site_type']
        )
        
        # Process and store data with all privacy levels
        site_db.process_and_store(
            data_path=config['data_path'],
            sample_size=None  # Use all data
        )
        
        databases.append(site_db)
    
    print("\n" + "="*70)
    print("SETUP COMPLETE!")
    print("="*70)
    print("\nSummary:")
    print("- 3 Site Databases created")
    print("- 4 Privacy level collections per database")
    print("- Total: 12 searchable collections")
    print("- Ready for privacy-preserving queries")
    
    return databases


def test_privacy_levels(databases):
    """
    Test different privacy levels with a sample query across all sites
    """
    print("\n" + "="*70)
    print("TESTING PRIVACY LEVELS")
    print("="*70)
    
    test_query = "Find patients with diabetes and elevated glucose"
    
    for db in databases:
        print(f"\n{db.site_name.upper()} - {db.site_type.upper()} SITE")
        print("-" * 40)
        
        for privacy_level in ['none', 'low', 'moderate', 'high']:
            results = db.query(test_query, privacy_level, n_results=1)
            
            if results and results['results']['documents']:
                doc = results['results']['documents'][0][0] if results['results']['documents'][0] else "No results"
                # Truncate for display
                doc_preview = doc[:150] + "..." if len(doc) > 150 else doc
                print(f"\n{privacy_level.upper()} Privacy (ε={results['epsilon']}):")
                print(f"  {doc_preview}")
            else:
                print(f"\n{privacy_level.upper()} Privacy: No results found")


def main():
    """
    Main function to set up and test the system
    """
    # Set up all sites
    databases = setup_all_sites()
    
    # Run tests
    test_privacy_levels(databases)
    
    print("\n" + "="*70)
    print("All databases and collections are ready for use!")
    print("="*70)


if __name__ == "__main__":
    main()
