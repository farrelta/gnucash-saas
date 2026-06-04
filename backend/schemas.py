"""
Pydantic schemas for request/response validation.

Every public API endpoint uses one of these schemas for structured
input validation and consistent JSON output.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ---------------------------------------------------------------------------
# Auth schemas
# ---------------------------------------------------------------------------


class UserRegister(BaseModel):
    """Body for the registration endpoint."""

    email: EmailStr
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    """Body for the login endpoint."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Public representation of a user (no password hash)."""

    id: int
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """JWT access token returned after login/register."""

    access_token: str
    token_type: str = "bearer"


# ---------------------------------------------------------------------------
# Session schemas
# ---------------------------------------------------------------------------


class SessionResponse(BaseModel):
    """Public representation of a container session."""

    id: int
    user_id: int
    session_token: Optional[str] = None
    container_name: Optional[str] = None
    status: str
    created_at: datetime
    last_activity: Optional[datetime] = None
    url: Optional[str] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# File schemas
# ---------------------------------------------------------------------------


class FileInfo(BaseModel):
    """Metadata for a single user file."""

    filename: str
    size: int
    modified_at: datetime


# ---------------------------------------------------------------------------
# Generic schemas
# ---------------------------------------------------------------------------


class MessageResponse(BaseModel):
    """Simple message envelope."""

    message: str
