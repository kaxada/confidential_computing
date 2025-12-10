from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import settings

Base = declarative_base()
engine = create_engine(settings.database_url, future=True, echo=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@contextmanager
def session_scope() -> Generator:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_session() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_schema() -> None:
    """Apply minimal schema patches for deployments without migrations."""
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    def add_column(table: str, column: str, ddl: str) -> None:
        """Add a column if it does not already exist."""
        if table not in table_names:
            return
        columns = {col["name"] for col in inspector.get_columns(table)}
        if column in columns:
            return
        with engine.connect() as conn:
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"))
            conn.commit()

    # user_logs
    add_column("user_logs", "request_metadata", "TEXT")
    add_column("user_logs", "details", "TEXT")

    # users
    add_column("users", "requested_privacy_level", "VARCHAR(50)")
    add_column("users", "temporary_role", "role")
    add_column("users", "temporary_privacy_level", "VARCHAR(50)")
    add_column("users", "role_expires_at", "TIMESTAMP WITH TIME ZONE")
    add_column("users", "request_reason", "TEXT")
    add_column("users", "approved", "INTEGER NOT NULL DEFAULT 0")

    # chat_threads
    add_column("chat_threads", "title", "VARCHAR(255)")

    # chat_messages
    add_column("chat_messages", "role", "VARCHAR(32)")
