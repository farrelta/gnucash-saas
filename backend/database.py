"""
Database configuration module.

Supports env-driven DATABASE_URL with automatic pool configuration
for SQLite (local dev) and production databases (MySQL/PostgreSQL).
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sessions.db")

# Build engine kwargs based on database type
engine_kwargs: dict = {
    "pool_pre_ping": True,
}

if DATABASE_URL.startswith("sqlite"):
    # SQLite requires check_same_thread=False for FastAPI
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # Production databases benefit from connection pooling
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

engine = create_engine(DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a database session and ensures cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
