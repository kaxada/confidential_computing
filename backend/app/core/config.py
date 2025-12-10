from pydantic_settings import BaseSettings

ROLE_METADATA = {
    "pi": {"label": "PI", "privacy_level": "none"},
    "admin": {"label": "Admin", "privacy_level": "none"},
    "researcher": {"label": "Researcher", "privacy_level": "low"},
    "clinician": {"label": "Clinician", "privacy_level": "low"},
    "analyst": {"label": "Analyst", "privacy_level": "moderate"},
    "auditor": {"label": "Auditor", "privacy_level": "moderate"},
    "student": {"label": "Student", "privacy_level": "high"},
    "intern": {"label": "Intern", "privacy_level": "high"},
}

PRIVACY_METADATA = {
    "none": {"label": "Full access"},
    "low": {"label": "Expanded access"},
    "moderate": {"label": "Balanced privacy"},
    "high": {"label": "Restricted access"},
}


class Settings(BaseSettings):
    jwt_secret: str = "dev-secret-change-me"  # replace in real deployments
    jwt_algorithm: str = "HS256"
    jwt_exp_minutes: int = 60
    site_base_url: str = "http://localhost:8080"  # overridden via .env for different sites
    site_id: str = "site_local"
    default_privacy_level: str = "moderate"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/confidential_rag"
    
    # Hub Configuration
    openai_api_key: str = ""
    aggregation_model: str = "gpt-4"
    
    # Site Registry (ID -> URL)
    site_registry: dict = {
        "site_1": {"url": "http://localhost:8080"},
        "site_2": {"url": "http://localhost:8081"},
        "site_3": {"url": "http://localhost:8082"}
    }

    # Site Metadata for Semantic Routing
    site_metadata: list = [
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

    class Config:
        env_file = ".env"


settings = Settings()


def get_access_payload(role) -> dict:
    # Accept Role enum or string
    role_value = getattr(role, "value", None) or (str(role).strip().lower() if role else None)
    role_meta = ROLE_METADATA.get(role_value)

    privacy_level = (role_meta or {}).get("privacy_level") or settings.default_privacy_level
    privacy_meta = PRIVACY_METADATA.get(privacy_level, {})

    role_label = (role_meta or {}).get("label") or role_value

    return {
        "role": role_value,
        "role_label": role_label,
        "privacy_level": privacy_level,
        "privacy_label": privacy_meta.get("label", privacy_level),
    }
