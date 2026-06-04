"""
SQLAlchemy ORM models for the GnuCash SaaS platform.

Models:
    - User: Registered platform users with hashed credentials.
    - Session: Container session records linking users to GnuCash instances.
    - AuditLog: Immutable audit trail for security-relevant actions.
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    """Registered user account."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    sessions = relationship("Session", back_populates="user")


class Session(Base):
    """GnuCash container session linked to a user."""

    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_token = Column(String(255))
    container_name = Column(String(255))
    container_id = Column(String(255))
    xpra_port = Column(Integer)
    status = Column(String(50), default="RUNNING")
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    internal_host = Column(String(255))
    internal_port = Column(Integer)

    user = relationship("User", back_populates="sessions")


class AuditLog(Base):
    """Immutable audit trail entry."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    detail = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
