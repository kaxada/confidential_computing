import os
import sys
import pathlib
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure backend package import
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from app.core import db, config
from app.core.db import Base, get_session


def pytest_sessionstart(session):
    # Point to sqlite in-memory for tests
    config.settings.database_url = "sqlite+pysqlite:///:memory:"


@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(
        config.settings.database_url,
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Override global engine/session factory used by app
    db.engine = engine
    db.SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="function", autouse=True)
def db_session(monkeypatch, db_engine):
    TestingSessionLocal = sessionmaker(bind=db_engine, autoflush=False, autocommit=False, future=True)
    session = TestingSessionLocal()

    def _get_session():
        try:
            yield session
        finally:
            pass

    monkeypatch.setattr("app.core.db.get_session", _get_session)
    try:
        yield session
    finally:
        session.close()
