from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    jwt_secret: str = "dev-secret-change-me"  # replace in real deployments
    jwt_algorithm: str = "HS256"
    jwt_exp_minutes: int = 60
    site_base_url: str = "http://localhost:9000"  # stub site service
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/confidential_rag"

    class Config:
        env_file = ".env"


settings = Settings()
