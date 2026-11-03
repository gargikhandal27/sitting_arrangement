"""
Database connection and session management.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from contextlib import contextmanager
from typing import Generator

from config import DATABASE_URL

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=False,          # Set True only for debugging SQL
    future=True,
)

# Session factory
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    future=True,
)

# Declarative base for all models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency-style session generator.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context-manager style session (preferred)."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    """Create all tables if they do not exist."""
    # Import models so that they are registered with Base.metadata
    from database import models  # noqa: F401
    Base.metadata.create_all(bind=engine)


def drop_all_tables() -> None:
    """Dangerous – only for development resets."""
    Base.metadata.drop_all(bind=engine)
