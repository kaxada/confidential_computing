# Confidential-Computing-Hub/populate_router.py
import requests

METADATA_DB_URL = "http://localhost:9001/add_site"

# The descriptions are now Data, not Code.
SITES = [
    {
        "text": "SPECIALTY: Laboratory & Pathology. Detailed blood work, urinalysis, biopsy reports, CMP, CBC, lipid profiles, and toxicology.",
        "metadata": {"site_id": "site_1", "url": "http://localhost:8080"}
    },
    {
        "text": "SPECIALTY: Clinical Diagnosis & Treatment. Physician notes, discharge summaries, ICD-10 diagnosis codes, treatment plans, prescriptions.",
        "metadata": {"site_id": "site_2", "url": "http://localhost:8081"}
    },
    {
        "text": "SPECIALTY: Demographics & History. Patient admission records, insurance details, emergency contacts, social history, and admin data.",
        "metadata": {"site_id": "site_3", "url": "http://localhost:8082"}
    }
]

print("Seeding Hub Metadata DB...")
for site in SITES:
    try:
        res = requests.post(METADATA_DB_URL, json=site)
        print(f"Added {site['metadata']['site_id']}: {res.json()}")
    except Exception as e:
        print(f"Error adding {site['metadata']['site_id']}: {e}")